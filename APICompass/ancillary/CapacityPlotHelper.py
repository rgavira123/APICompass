import re
from typing import List, Optional, Union
import plotly.graph_objects as go
from matplotlib.colors import to_rgba
from APICompass.ancillary.time_unit import TimeUnit
from APICompass.utils import parse_time_string_to_duration

class CapacityPlotHelper:

    @staticmethod
    def adjust_x_axis(x_vals):
        range_val = max(x_vals) - min(x_vals)
        minimum = min([x for x in x_vals if x > 0], default=0)

        if range_val < 3600 or minimum < 3600:
            return 60, "Time (min)"
        elif range_val < 86400 or minimum < 86400:
            return 3600, "Time (h)"
        elif range_val < 2592000 or minimum < 2592000:
            return 86400, "Time (days)"
        else:
            return 2592000, "Time (months)"

    @staticmethod
    def scale(values, factor):
        return [v / factor for v in values]

    @staticmethod
    def add_month_lines(fig, num_months, month_duration_seconds, scale):
        for month in range(1, num_months):
            fig.add_vline(
                x=(month * month_duration_seconds) / scale,
                line=dict(color="gray", width=1, dash="dot")
            )

    @staticmethod
    def format_y_value(value):
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        elif value >= 1_000:
            return f"{value / 1_000:.1f}k"
        return str(value)

    @staticmethod
    def format_time_tooltip(seconds):
        if seconds < 60:
            return f"{seconds:.0f} s"
        elif seconds < 3600:
            return f"{seconds / 60:.1f} min"
        elif seconds < 86400:
            return f"{seconds / 3600:.1f} h"
        elif seconds < 2592000:
            return f"{seconds / 86400:.1f} days"
        else:
            return f"{seconds / 2592000:.1f} months"
    @staticmethod
    def rename_and_style_traces(fig, names=None, colors=None, dashes=None):
        """
        Renames and styles the traces of a Plotly figure.
        :param fig: The Plotly figure to update.
        :param names: List of names for the traces.
        :param colors: List of colors for the traces.
        :param dashes: List of dash styles for the traces.
        """
        for i, trace in enumerate(fig.data):
            if names and i < len(names):
                trace.name = names[i]
            if colors and i < len(colors):
                trace.line.color = colors[i]
            if dashes and i < len(dashes):
                trace.line.dash = dashes[i]

    @staticmethod
    def place_legend(fig, inside=True, position="top right"):
        if inside:
            positions = {
                "top right": dict(x=0.98, y=0.98, xanchor="right", yanchor="top"),
                "top left": dict(x=0.02, y=0.98, xanchor="left", yanchor="top"),
                "bottom right": dict(x=0.98, y=0.02, xanchor="right", yanchor="bottom"),
                "bottom left": dict(x=0.02, y=0.02, xanchor="left", yanchor="bottom")
            }
            opts = positions.get(position, positions["top right"])
            fig.update_layout(legend=dict(
                orientation="v",
                bgcolor="rgba(255,255,255,0.7)",
                bordercolor="black",
                borderwidth=1,
                **opts
            ))
        else:
            fig.update_layout(legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.1,
                xanchor="center",
                x=0.5
            ))
  
    @staticmethod
    def get_figure_template(title=None, yaxis_title=None, xaxis_title=None):
        return {
            "layout": {
                "title": {"text": title, "font": {"size": 18}} if title else None,
                "xaxis": {
                    "title": xaxis_title,
                    "showgrid": True,
                    "zeroline": False,
                    "showline": True,
                    "mirror": True
                },
                "yaxis": {
                    "title": yaxis_title,
                    "showgrid": True,
                    "zeroline": False,
                    "showline": True,
                    "mirror": True
                },
                "legend": {
                    "bgcolor": "rgba(255,255,255,0.7)",
                    "bordercolor": "black",
                    "borderwidth": 1
                },
                "plot_bgcolor": "white",
                "margin": {"l": 60, "r": 40, "t": 60, "b": 60},
                "font": {"family": "Arial", "size": 12}
            }
        }
    '''
    @staticmethod
    def apply_template(fig, title=None, yaxis_title=None, xaxis_title=None):
        template = CapacityPlotHelper.get_figure_template(title, yaxis_title, xaxis_title)
    '''
    @staticmethod
    def apply_template(fig, title=None, yaxis_title=None, xaxis_title=None):
        template = CapacityPlotHelper.get_figure_template(title, yaxis_title, xaxis_title)
        fig.update_layout(**{k: v for k, v in template["layout"].items() if v is not None})

    @staticmethod
    def get_dark_theme_template(title=None, yaxis_title=None, xaxis_title=None):
        return {
            "layout": {
                "template": "plotly_dark",
                "title": {"text": title, "font": {"size": 18, "color": "white"}} if title else None,
                "xaxis": {
                    "title": xaxis_title,
                    "showgrid": True,
                    "zeroline": False,
                    "showline": True,
                    "mirror": True,
                    "color": "white"
                },
                "yaxis": {
                    "title": yaxis_title,
                    "showgrid": True,
                    "zeroline": False,
                    "showline": True,
                    "mirror": True,
                    "color": "white"
                },
                "legend": {
                    "bgcolor": "rgba(50,50,50,0.7)",
                    "bordercolor": "white",
                    "borderwidth": 1,
                    "font": {"color": "white"}
                },
                "plot_bgcolor": "#222",
                "paper_bgcolor": "#222",
                "margin": {"l": 60, "r": 40, "t": 60, "b": 60},
                "font": {"family": "Arial", "size": 12, "color": "white"}
            }
        }
    @staticmethod
    def add_v_line(fig, x, color="gray", dash="dot", width=1, annotation_text=None, annotation_position="top right"):
        fig.add_vline(
            x=x,
            line=dict(color=color, width=width, dash=dash)
        )
        if annotation_text:
            pos = {
                "top right": dict(xanchor="right", yanchor="top"),
                "top left": dict(xanchor="left", yanchor="top"),
                "bottom right": dict(xanchor="right", yanchor="bottom"),
                "bottom left": dict(xanchor="left", yanchor="bottom"),
            }.get(annotation_position, {})
            fig.add_annotation(
                x=x,
                y=1,
                text=annotation_text,
                showarrow=True,
                yref="paper",
                **pos
            )

    @staticmethod
    def add_h_line(fig, y, color="gray", dash="dot", width=1, annotation_text=None, annotation_position="right top"):
        fig.add_hline(
            y=y,
            line=dict(color=color, width=width, dash=dash)
        )
        if annotation_text:
            pos = {
                "right top": dict(xanchor="right", yanchor="top"),
                "left top": dict(xanchor="left", yanchor="top"),
                "right bottom": dict(xanchor="right", yanchor="bottom"),
                "left bottom": dict(xanchor="left", yanchor="bottom"),
            }.get(annotation_position, {})
            fig.add_annotation(
                y=y,
                x=1,
                text=annotation_text,
                showarrow=True,
                xref="paper",
                **pos
            )

    @staticmethod
    def show_line(
        fig: go.Figure,
        *,
        x: Optional[str] = None,
        y: Optional[float] = None,
        color: str = "red",
        dash: str = "dash",
        width: int = 1,
        opacity: float = 1.0,
        layer: str = "above",
        annotation_text: Optional[str] = None,
        annotation_position: Optional[str] = None,
        annotation_font: Optional[dict] = None,
        annotation_align: Optional[str] = None,
        row: Optional[int] = None,   # ← NUEVO
        col: Optional[int] = None    # ← NUEVO
    ) -> None:
        title = fig.layout.xaxis.title.text or ""
        m = re.search(r"\((ms|s|min|h|day|week|month|year)\)", title)
        tgt = TimeUnit(m.group(1)) if m else TimeUnit.SECOND

        if x is not None:
            td = parse_time_string_to_duration(x)
            td_conv = td.to_desired_time_unit(tgt)
            fig.add_vline(
                x=td_conv.value,
                line=dict(color=color, dash=dash, width=width),
                opacity=opacity,
                layer=layer,
                annotation_text=annotation_text,
                annotation_position=annotation_position,
                annotation_font=annotation_font,
                annotation_align=annotation_align,
                row=row,  # ← esto hace que se aplique al subplot correcto
                col=col
            )

        if y is not None:
            fig.add_hline(
                y=y,
                line=dict(color=color, dash=dash, width=width),
                opacity=opacity,
                layer=layer,
                annotation_text=annotation_text,
                annotation_position=annotation_position,
                annotation_font=annotation_font,
                annotation_align=annotation_align,
                row=row,
                col=col
            )


    @staticmethod
    def update_legend_names(fig: go.Figure, legend_names: List[str]) -> None:
        traces = fig.data
        rate_idx = 0
        i = 0
        while i < len(traces) and rate_idx < len(legend_names):
            name = legend_names[rate_idx]
            if i + 1 < len(traces) and traces[i+1].name.startswith("Instantaneous"):
                traces[i].name = name
                traces[i].legendgroup = name
                traces[i+1].name = name
                traces[i+1].legendgroup = name
                i += 2
            else:
                traces[i].name = name
                traces[i].legendgroup = name
                i += 1
            rate_idx += 1

    @staticmethod
    def update_legend(fig: go.Figure, legend_title: str) -> None:
        fig.update_layout(legend_title=dict(text=legend_title))

    @staticmethod
    def update_yaxis(fig: go.Figure, yaxis_title: str) -> None:
        fig.update_layout(yaxis_title=yaxis_title)

    @staticmethod
    def update_title(fig: go.Figure, title: str) -> None:
        fig.update_layout(title=title)

