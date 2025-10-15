from typing import List, Optional, Union
from APICompass.ancillary.time_unit import TimeDuration, TimeUnit
from APICompass.basic.bounded_rate import BoundedRate, Rate, Quota
from APICompass.utils import parse_time_string_to_duration, select_best_time_unit
from APICompass.basic.compare_curves import *
import plotly.graph_objects as go

class Plan():
    def __init__(self, name, bounded_rate: BoundedRate, cost, overage_cost, max_number_of_subscriptions, billing_period):
        self.name = name
        self.bounded_rate = bounded_rate
        self.cost = cost
        self.overage_cost = overage_cost
        self.max_number_of_subscriptions = max_number_of_subscriptions
        self.billing_period = billing_period
        self.max_included_quota: Optional[int] = None

    
    def show_capacity_inflection_points(self, time_interval: Union[str, TimeDuration], return_fig=False):
        if isinstance(time_interval, str):
            time_interval = parse_time_string_to_duration(time_interval)
        return self.bounded_rate.show_capacity_from_inflection_points(time_interval, return_fig=return_fig)
    
    def quota_exhaustion_thresholds(self):
        return self.bounded_rate.quota_exhaustion_threshold()
    
    def capacity_at(self, time_interval: Union[str, TimeDuration]):
        if isinstance(time_interval, str):
            time_interval = parse_time_string_to_duration(time_interval)
        return self.bounded_rate.capacity_at(time_interval)
    
    def capacity_during(self, time_interval: Union[str, TimeDuration]):
        if isinstance(time_interval, str):
            time_interval = parse_time_string_to_duration(time_interval)
        return self.bounded_rate.capacity_during(time_interval)
    
    def min_time(self, capacity_goal):
        return self.bounded_rate.min_time(capacity_goal)

    def show_capacity(self, time_interval: Union[str, TimeDuration], return_fig=False):
        if isinstance(time_interval, str):
            time_interval = parse_time_string_to_duration(time_interval)
        
        return self.bounded_rate.show_capacity(time_interval, return_fig=return_fig)

    def consume(self, demand: 'Demand', time_interval: Union[str, TimeDuration],return_fig=False):
        """
        Consumes demand over a specified time interval, comparing bounded rates.

        Args:
            demand (Demand): The demand to consume.
            time_interval (Union[str, TimeDuration]): The time interval for consumption.
        """
        if isinstance(time_interval, str):
            time_interval = parse_time_string_to_duration(time_interval)

        # Compare the bounded rates of the plan and the demand
        fig = compare_bounded_rates_capacity(
            bounded_rates=[self.bounded_rate, demand.bounded_rate],
            time_interval=time_interval,
            return_fig=return_fig
        )
        
        if return_fig:
            return fig
    
    def compare_demands(self, demands: List['Demand'], time_interval: Optional[Union[str, TimeDuration]] = None, return_fig=False):
        """
        Compares multiple demands over a specified time interval.

        Args:
            demands (List[Demand]): The list of demands to compare.
            time_interval (Optional[Union[str, TimeDuration]]): The time interval for comparison. Defaults to None.
        """
        if time_interval is None:
            max_limit_plan = self.bounded_rate.limits[-1].consumption_period.to_milliseconds()
            if self.bounded_rate.max_active_time:
                max_limit_plan = max(max_limit_plan, self.bounded_rate.max_active_time.to_milliseconds())

            for demand in demands:
                max_limit_demand = demand.bounded_rate.limits[-1].consumption_period.to_milliseconds()
                if demand.bounded_rate.max_active_time:
                    max_limit_demand = max(max_limit_demand, demand.bounded_rate.max_active_time.to_milliseconds())

                max_limit_plan = max(max_limit_plan, max_limit_demand)

            time_interval = TimeDuration(max_limit_plan, TimeUnit.MILLISECOND)
            time_interval = select_best_time_unit(time_interval.to_milliseconds())
        elif isinstance(time_interval, str):
            time_interval = parse_time_string_to_duration(time_interval)

        # Compare the bounded rates of the plan and the demand
        fig = compare_bounded_rates_capacity(
            bounded_rates=[self.bounded_rate] + [demand.bounded_rate for demand in demands],
            time_interval=time_interval,
            return_fig=return_fig
        )
        
        if return_fig:
            return fig
    
    def has_enough_capacity_for_constant_rate(
        self,
        demand: 'Demand',
        time_interval: Union[str, TimeDuration, None] = None
    ) -> None:
        """
        Check if this plan can serve a constant‐rate demand over the demand's duration.
        Prints Yes or No and the first point of failure (if any).
        """
        # 1) Si no viene intervalo, usamos la duración de la demanda
        if time_interval is None:
            time_interval = demand.bounded_rate.max_active_time
            if time_interval is None:
                raise ValueError("Demand has no max_active_time; please supply time_interval.")
        elif isinstance(time_interval, str):
            time_interval = parse_time_string_to_duration(time_interval)

        # 2) Extraemos curvas debug [(t_ms, cap), ...]
        plan_pts = self.bounded_rate.show_available_capacity_curve(time_interval, debug=True)
        dem_pts  = demand.bounded_rate.show_available_capacity_curve(time_interval, debug=True)

        unit_ms = time_interval.unit.to_milliseconds()

        # 3) Recorremos punto a punto
        for (t_ms, cap_plan), (_, cap_dem) in zip(plan_pts, dem_pts):
            t_val = t_ms / unit_ms
            if cap_dem > cap_plan:
                print(
                    f"No: at t={t_val:.2f}{time_interval.unit.value}, "
                    f"plan={cap_plan}, demand={cap_dem}"
                )
                return

        # 4) Si nunca falla
        print(
            f"Yes: plan covers demand up to "
            f"{time_interval.value}{time_interval.unit.value}."
        )
    
    def has_enough_capacity(
        self,
        demand: 'Demand',
        output_time_unit: TimeUnit = TimeUnit.SECOND
    ) -> dict:
        """
        Analyze whether the plan can cover the demand, returning a dict with:
        - can_cover (bool)
        - plan_rate (str)
        - demand_rate (str)
        - v_plan (float): plan speed in req/ms
        - v_demand (float): demand speed in req/ms
        - max_backlog (int)
        - drain_time (float, in output_time_unit)
        - scheduled_requests (List[{"id": int, "scheduled_at": float}])
        - resume_plan_rate (str)
        - resume_in (float, in output_time_unit)
        """
        # 0) Instantaneous rate check
        plan_rate = self.bounded_rate.rate
        d_rate = demand.bounded_rate.rate
        v_plan = plan_rate.consumption_unit / plan_rate.consumption_period.to_milliseconds()
        v_dem = d_rate.consumption_unit / d_rate.consumption_period.to_milliseconds()

        if v_dem > v_plan:
            return {
                "can_cover": False,
                "plan_rate": f"{plan_rate.consumption_unit}/{plan_rate.consumption_period}",
                "demand_rate": f"{d_rate.consumption_unit}/{d_rate.consumption_period}",
                "v_plan": round(v_plan, 6),
                "v_demand": round(v_dem, 6),
                "reason": "instantaneous_rate_exceeded"
            }

        # 1) Quota comparison
        plan_quotas = self.bounded_rate.quota or []
        if isinstance(plan_quotas, Quota):
            plan_quotas = [plan_quotas]
        demand_quotas = demand.bounded_rate.quota or []
        if isinstance(demand_quotas, Quota):
            demand_quotas = [demand_quotas]
        for q_d in demand_quotas:
            for q_p in plan_quotas:
                ms_d = q_d.consumption_period.to_milliseconds()
                ms_p = q_p.consumption_period.to_milliseconds()
                if ms_d >= ms_p:
                    scaled = q_d.consumption_unit * (ms_p / ms_d)
                    if scaled > q_p.consumption_unit:
                        return {
                            "can_cover": False,
                            "plan_rate": f"{plan_rate.consumption_unit}/{plan_rate.consumption_period}",
                            "demand_rate": f"{d_rate.consumption_unit}/{d_rate.consumption_period}",
                            "v_plan": round(v_plan, 6),
                            "v_demand": round(v_dem, 6),
                            "reason": "quota_exceeded",
                            "quota_plan": f"{q_p.consumption_unit} per {q_p.consumption_period}",
                            "quota_demand": f"{q_d.consumption_unit} per {q_d.consumption_period}",
                            "quota_equiv_demand_in_plan_window": round(scaled, 2),
                            "quota_allowed_in_plan_window": q_p.consumption_unit
                        }
                else:
                    scaled = q_p.consumption_unit * (ms_d / ms_p)
                    if q_d.consumption_unit > scaled:
                        return {
                            "can_cover": False,
                            "plan_rate": f"{plan_rate.consumption_unit}/{plan_rate.consumption_period}",
                            "demand_rate": f"{d_rate.consumption_unit}/{d_rate.consumption_period}",
                            "v_plan": round(v_plan, 6),
                            "v_demand": round(v_dem, 6),
                            "reason": "quota_exceeded",
                            "quota_plan": f"{q_p.consumption_unit} per {q_p.consumption_period}",
                            "quota_demand": f"{q_d.consumption_unit} per {q_d.consumption_period}",
                            "quota_equiv_demand_in_plan_window": round(scaled, 2),
                            "quota_allowed_in_plan_window": q_p.consumption_unit
                        }

        # 2) Horizon and sampling
        plan_q_ms = plan_quotas[0].consumption_period.to_milliseconds() if plan_quotas else 0
        demand_q_ms = demand_quotas[-1].consumption_period.to_milliseconds() if demand_quotas else 0
        horizon_ms = max(plan_q_ms, demand_q_ms)
        td = select_best_time_unit(horizon_ms)
        step_ms = plan_rate.consumption_period.to_milliseconds()
        times = list(range(0, int(td.to_milliseconds()) + 1, int(step_ms)))
        if times[-1] != td.to_milliseconds():
            times.append(int(td.to_milliseconds()))

        plan_pts = self.bounded_rate.show_available_capacity_curve(td, debug=True)
        demand_pts = demand.bounded_rate.show_available_capacity_curve(td, debug=True)

        def value_at(ts, pts):
            last = 0
            for t, c in pts:
                if t > ts:
                    break
                last = c
            return last

        # 3) Compute backlog
        max_backlog = 0
        for t in times:
            back = value_at(t, demand_pts) - value_at(t, plan_pts)
            if back > max_backlog:
                max_backlog = back

        if max_backlog <= 0:
            return {
                "can_cover": True,
                "plan_rate": f"{plan_rate.consumption_unit}/{plan_rate.consumption_period}",
                "demand_rate": f"{d_rate.consumption_unit}/{d_rate.consumption_period}",
                "v_plan": round(v_plan, 6),
                "v_demand": round(v_dem, 6),
                "max_backlog": 0,
                "scheduled_requests": [],
                "resume_plan_rate": f"{plan_rate.consumption_unit}/{plan_rate.consumption_period}",
                "resume_in": 0.0
            }

        # 4) Drain backlog
        r_p = v_plan
        periodo_ms = 1 / r_p
        t_drain_ms = max_backlog / r_p

        # 5) Schedule requests
        scheduled = []
        first_id = 2
        for i in range(int(max_backlog)):
            pid = first_id + i
            t_i_ms = (i + 1) * periodo_ms
            t_i = TimeDuration(t_i_ms, TimeUnit.MILLISECOND)\
                    .to_desired_time_unit(output_time_unit).value
            scheduled.append({"id": pid, "scheduled_at": t_i})

        # 6) Resume windows
        dp_ms = d_rate.consumption_period.to_milliseconds()
        rem_ms = dp_ms - (t_drain_ms % dp_ms)
        if rem_ms >= dp_ms:
            rem_ms = 0
        resume_in = TimeDuration(rem_ms, TimeUnit.MILLISECOND)\
                        .to_desired_time_unit(output_time_unit).value

        return {
            "can_cover": True,
            "plan_rate": f"{plan_rate.consumption_unit}/{plan_rate.consumption_period}",
            "demand_rate": f"{d_rate.consumption_unit}/{d_rate.consumption_period}",
            "v_plan": round(v_plan, 6),
            "v_demand": round(v_dem, 6),
            "max_backlog": int(max_backlog),
            "drain_time": TimeDuration(t_drain_ms, TimeUnit.MILLISECOND)
                        .to_desired_time_unit(output_time_unit).value,
            "scheduled_requests": scheduled,
            "resume_plan_rate": f"{plan_rate.consumption_unit}/{plan_rate.consumption_period}",
            "resume_in": resume_in
        }

        
    def info_has_enough_capacity(
        self,
        demand: 'Demand',
        output_time_unit: TimeUnit = TimeUnit.SECOND
    ) -> None:
        """
        Prints a human-readable summary of has_enough_capacity(demand)
        using the analysis dictionary returned.
        """
        analysis = self.has_enough_capacity(demand, output_time_unit)

        print("\n=== Capacity Analysis: Plan vs Demand ===\n")

        plan_rate = self.bounded_rate.rate
        d_rate = demand.bounded_rate.rate

        v_plan = plan_rate.consumption_unit / plan_rate.consumption_period.to_milliseconds()
        v_dem = d_rate.consumption_unit / d_rate.consumption_period.to_milliseconds()

        if not analysis.get("can_cover"):
            print(f"✘ Demand cannot be served.\n→ Reason: {analysis.get('reason', 'unspecified')}")
            print(f"→ Plan rate:   {analysis.get('plan_rate')}")
            print(f"→ Demand rate: {analysis.get('demand_rate')}")

            if analysis["reason"] == "quota_exceeded":
                print(f"→ Plan quota:      {analysis['quota_plan']}")
                print(f"→ Demand quota:    {analysis['quota_demand']}")
                print(f"→ In the plan's window, demand requires ~{analysis['quota_equiv_demand_in_plan_window']} requests")
                print(f"→ But the plan only allows {analysis['quota_allowed_in_plan_window']} requests\n")
            return


        print(f"✔ Demand CAN be served within the plan limits.\n")
        print(f"→ Plan rate:   {plan_rate.consumption_unit}/{plan_rate.consumption_period} → {v_plan:.6f} req/ms")
        print(f"→ Demand rate: {d_rate.consumption_unit}/{d_rate.consumption_period} → {v_dem:.6f} req/ms")
        
        max_backlog = analysis.get("max_backlog")
        drain_time = analysis.get("drain_time")
        resume_in = analysis.get("resume_in")
        resume_plan_rate = analysis.get("resume_plan_rate")

        print(f"→ Max backlog: {max_backlog if max_backlog is not None else 'N/A'} requests")

        if drain_time is not None:
            print(f"→ Time to drain backlog: {drain_time:.2f} {output_time_unit.value}")
        else:
            print(f"→ Time to drain backlog: N/A")

        scheduled = analysis.get("scheduled_requests", [])
        if scheduled:
            print("\nRescheduled requests (ID → time):")
            for r in scheduled:
                print(f"  · Request #{r['id']}: at {r['scheduled_at']:.2f} {output_time_unit.value}")
            last_id = scheduled[-1]['id']
            print(f"\n✔ After request #{last_id}, backlog is cleared.")
        else:
            print("\n✔ No rescheduling required.")

        if resume_in is not None:
            print(f"→ Resume regular demand after {resume_in:.2f} {output_time_unit.value}")
        else:
            print("→ Resume regular demand: N/A")

        if resume_plan_rate is not None:
            print(f"→ Resume at plan rate: {resume_plan_rate}")
        else:
            print("→ Resume at plan rate: N/A")

        print()


        
    
    def plot_rescheduled_capacity(
        self,
        demand: 'Demand',
        time_interval: Union[str, TimeDuration],
        output_time_unit: TimeUnit = TimeUnit.SECOND
    ) -> go.Figure:
        """
        Generates and returns a Plotly figure showing:
        - Plan capacity curve
        - Original demand curve
        - Rescheduled demand curve (with enqueued requests)
        """
        # Convert time_interval if needed
        if isinstance(time_interval, str):
            time_interval = parse_time_string_to_duration(time_interval)
        td = select_best_time_unit(time_interval.to_milliseconds())
        
        # Sampled curves (debug)
        plan_pts = self.bounded_rate.show_available_capacity_curve(td, debug=True)
        demand_pts = demand.bounded_rate.show_available_capacity_curve(td, debug=True)
        
        times_ms = [t for t, _ in plan_pts]
        plan_caps = [c for _, c in plan_pts]
        demand_caps = [c for _, c in demand_pts]
        
        # Analyze capacity to get scheduled requests
        analysis = self.has_enough_capacity(demand, output_time_unit)
        scheduled = analysis.get("scheduled_requests", [])
        
        # Build rescheduled demand
        demand_resched = []
        cum = 0
        sched_iter = iter(scheduled)
        next_sched = next(sched_iter, None)
        for t_ms, orig_c in zip(times_ms, demand_caps):
            if t_ms == 0:
                cum = orig_c
            while next_sched and next_sched["scheduled_at"] * 1000 <= t_ms:
                cum += 1
                next_sched = next(sched_iter, None)
            demand_resched.append(cum)
        
        # Convert times to output unit for axis
        factor = output_time_unit.to_milliseconds(1)
        xs = [t / factor for t in times_ms]
        
        # Create figure
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=xs, y=plan_caps, mode="lines", name="Plan Capacity",
            line=dict(color="green", shape="hv")
        ))
        fig.add_trace(go.Scatter(
            x=xs, y=demand_caps, mode="lines", name="Original Demand",
            line=dict(color="blue", dash="dash", shape="hv")
        ))
        fig.add_trace(go.Scatter(
            x=xs, y=demand_resched, mode="lines", name="Rescheduled Demand",
            line=dict(color="red", shape="hv")
        ))

        fig.update_layout(
            title="Capacity vs. Rescheduled Demand",
            xaxis_title=f"Time ({output_time_unit.value})",
            yaxis_title="Accumulated Requests",
            legend_title="Curves",
            template="plotly_white"
        )
        
        fig.show()


class Demand():
    def __init__(
        self,
        rate: Union[Rate, int],
        consumption_period: Union[str, TimeDuration, None] = None,
        duration: Union[str, TimeDuration, None] = None,
        quota: Union[Quota, List[Quota], None] = None,
        N: int = None,
    ):
        # nueva sobrecarga: si me pasan un int, lo convierto en Rate
        if isinstance(rate, int):
            if consumption_period is None:
                raise ValueError("Cuando llamas Demand(1, ...), debes pasar también el periodo, p.ej. '3s'")
            # parsear string a TimeDuration si hace falta
            if isinstance(consumption_period, str):
                consumption_period = parse_time_string_to_duration(consumption_period)
            rate = Rate(rate, consumption_period)

        # parsear duration si vino como string
        if isinstance(duration, str):
            duration = parse_time_string_to_duration(duration)
        self.duration = duration

        # mantenemos la lógica antigua para quota y N
        if N is not None:
            self.rate = Rate(rate.consumption_unit * N, rate.consumption_period)
            self.quota = None if quota is None else (quota if isinstance(quota, list) else [quota])
            if self.quota is not None:
                self.quota = [
                    Quota(q.consumption_unit * N, q.consumption_period)
                    for q in self.quota
                ]
        else:
            self.rate = rate
            self.quota = None if quota is None else (quota if isinstance(quota, list) else [quota])

        # ahora creamos el bounded_rate pasando max_active_time=self.duration
        self.bounded_rate = BoundedRate(
            self.rate,
            self.quota,
            max_active_time=self.duration
        )

            
    def __str__(self):
        return f"Demand(rate={self.rate}, quota={self.quota})"

    def show_capacity(self, time_interval: Union[str, TimeDuration]):
        """
        Shows the capacity curve for the demand.

        Args:
            time_interval (Union[str, TimeDuration]): The time interval for the capacity curve.
        """
        if isinstance(time_interval, str):
            time_interval = parse_time_string_to_duration(time_interval)

        return self.bounded_rate.show_capacity(time_interval)
    
    def multiply_by(self, n: int):
        """
        Multiplies the demand by a given factor, as if it were multiple users.
        
        Args:
            n (int): The factor to multiply the demand by.
            
        Returns:
            Demand: A new Demand instance with the multiplied rate and quota. (Bounded Rate)
        """
        
        if n <= 0:
            raise ValueError("The number of users must be a positive integer.")
        
        return Demand(rate=self.rate, quota=self.quota, N=n)

# Example usage
if __name__ == "__main__":

    # Create a BoundedRate instance for testing
    plan_limits = BoundedRate(Rate(1, "2s"), Quota(1500, "1h"))
    demand = Demand(1, "3s", "5min")
    demand2 = Demand(10, "1min", "100min")
    demand3 = Demand(100, "1min", "10min")
    demand4 = Demand(1, "2s", "1h")

    # Create a Plan instance
    plan = Plan("Test Plan", plan_limits, cost=100, overage_cost=10, max_number_of_subscriptions=1, billing_period="1 month")

 
    fig = plan.compare_demands([demand, demand2, demand3, demand4], return_fig=True)
    
    update_title(fig, "Plan vs Demands")
    update_yaxis(fig, "Requests")
    #update_legend_names(fig, ["Demand 3", "Plan", "Demand 4", "Demand 1", "Demand 2"])
    update_legend(fig, "Bounded Rates")
    fig.show()

    
    
    




