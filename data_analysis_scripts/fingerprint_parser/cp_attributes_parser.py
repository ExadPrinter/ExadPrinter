class CpAttributeParser:  
    SETTINGS_CP_ATTRIBUTES = [
        "content://settings/system/alarm_alert", "content://settings/system/notification_sound", 
        "content://settings/secure", "content://settings/global","content://settings/system",
        "content://settings/system/ringtone"
    ]
    @classmethod
    def isCpAttribute(cls,key): 
        return key.startswith("content://")
    
    @classmethod
    def parse(cls,key,value): 
        try:
            if not cls.isCpAttribute(key):
                return None
            elif cls.__is_skipped(value):
                return None
            elif key in cls.SETTINGS_CP_ATTRIBUTES:
                return cls.__parse_settings_cp(value)
            else: 
                # Just mark it as not empty
                return 1
        except Exception as e:
            return None
    
    @staticmethod
    def __is_skipped(value):
        SKIPPED = ["MNC", "FNC", "ERR", "NULL","UNDEFINED"]
        if value == None:
            return True
        elif isinstance(value, str): 
            return not value or value.upper() in SKIPPED
        elif isinstance(value, (list, dict)) and len(value) == 0:
            return True
        elif isinstance(value, list):
            return all(not line or line in SKIPPED for line in value)
        else:
            return False
    
    @classmethod
    def __parse_settings_cp(cls, value):
        if isinstance(value, list):
            parsed_value = {}
            for item in value:
                if isinstance(item, dict):
                    if "name" in item and "value" in item:
                        n = item.get("name")
                        v = item.get("value")
                        parsed_value[n] = v
            return parsed_value if not cls.__is_skipped(parsed_value) else None
        else: 
            return value
        
        