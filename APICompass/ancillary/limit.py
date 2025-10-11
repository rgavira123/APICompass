from APICompass.ancillary.time_unit import TimeDuration, TimeUnit


class Limit:
    def __init__(self, value: int, duration: TimeDuration):
        self.__value = value
        self.__duration = duration

        
    @property
    def value(self):
        return self.__value
    
    @property
    def duration(self):
        return self.__duration
    
    @property
    def to_tuple(self):
        return (self.value, self.duration.to_seconds())
    
    def to_milliseconds(self):
        return self.duration.to_milliseconds()


    def __str__(self):
        return f"{self.value} calls per {self.duration.value} {self.duration.unit.name}"
    
    
if __name__ == "__main__":
    limit = Limit(100, TimeDuration(1, TimeUnit.HOUR))
    print(limit)
    print(limit.to_tuple)

