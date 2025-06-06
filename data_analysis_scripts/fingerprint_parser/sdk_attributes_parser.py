from fingerprint_parser.shell_attributes_parser import ShellAttributeParser
import re

class SdkAttributeParser:
    IGNORED_SDK_ATTRIBUTES = [
        "android.content.ClipboardManager.getPrimaryClip", 
        "android.content.ClipboardManager.getText", 
        "android.text.ClipboardManager.getPrimaryClip", 
        "android.text.ClipboardManager.getText",
    ]
    SPECIAL_ATTRIBUTES = [
        "isDeviceRooted", "execution_time", "uuid", "timestamp", "nbSdk",
        "isDeveloperModeEnabled", "isDeviceVirtual", "structureSdk"
    ]
                
    @classmethod
    def isSdkAttribute(cls,key): 
        if key in cls.SPECIAL_ATTRIBUTES:
            return False
        elif ShellAttributeParser.isShellAttribute(key):
            return False
        elif key.startswith("content://"):
            return False
        return  True
    
    @classmethod
    def parse(cls,key,value): 
        try:
            if not cls.isSdkAttribute(key):
                return None
            elif cls.__is_skipped(value):
                return None
            elif "getStackTrace" in key:
                return None
            elif key in cls.IGNORED_SDK_ATTRIBUTES:
                return None
            elif isinstance(value,str):
                return cls.__parse_str(value)
            elif isinstance(value,dict):
                return cls.__parse_dict(value)
            elif isinstance(value,list):
                if key == "android.accounts.AccountManager.getAccounts":
                    return value
                return cls.__parse_list(value)
            else: 
                return value
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
    def __parse_str(cls,value):
        try:   
            if not isinstance(value,str):
                raise Exception(f"type {type(value)} Not a str")
            value = value.strip()
            if value.lower() in ["true", "false"]:
                return value.lower() == "true"
            # Skip output of toStrings
            # Regex for standard object toString() pattern: "ClassName@HexCode"
            object_pattern = re.compile(r"^([\w$.]+)@[0-9a-fA-F]+$")

            # Regex for array toString() pattern:
            # - Object arrays: "[LClassName;@HexCode"
            # - Primitive arrays: "[I@HexCode", "[D@HexCode", etc.
            # - Multi-dimensional arrays: "[[I@HexCode", "[[LClassName;@HexCode", etc.
            array_pattern = re.compile(r"^(\[+L?[\w$.]+);?@[0-9a-fA-F]+$")
            
            match_object = object_pattern.match(value)
            match_array = array_pattern.match(value)
            if match_object or match_array:
                return None
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except:
                modules = cls.__extract_module_names(value)
                if len(modules)>0:
                    return modules[0] if len(modules) ==1 else modules
                else:
                    packages = cls.__getPackages(value)
                    if len(packages) > 0 : 
                        return packages[0] if len(packages) ==1 else packages
                return value
        except Exception as e: 
            return None
        
    @staticmethod
    def __extract_module_names(text: str):
        # Define regex pattern to capture module names
        pattern = r'\w+Info\{[\w]+ ([^}]+)\}'
        
        # Find all matches using regex
        module_names = re.findall(pattern, text)
        return module_names
    @staticmethod
    def __getPackages(data):
        # Regex to extract package names (at least one dot and word characters/digits/underscores)
        pattern = re.compile(r'\b([a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+)\b')
        return pattern.findall(data)

    @classmethod
    def __parse_list(cls, value):
        try : 
            if not isinstance(value,list):
                raise Exception(f"type {type(value)} Not a list")
            parsed_value = []
            for item in value : 
                if not  cls.__is_skipped(item):
                    if isinstance(item,str):
                        parsed_str = cls.__parse_str(item)
                        if not cls.__is_skipped(parsed_str):
                            if isinstance(parsed_str,list):
                                parsed_value.extend(cls.__parse_str(item))
                            else: 
                                parsed_value.append(cls.__parse_str(item))
                    elif isinstance(item,dict): 
                        if not cls.__is_skipped(cls.__parse_dict(item)):
                            parsed_value.append(cls.__parse_dict(item))
                    else: 
                        if not cls.__is_skipped(item):
                            parsed_value.append(item)
            parsed_value = list(set(parsed_value))
            return parsed_value if not cls.__is_skipped(parsed_value) else None
        except Exception as e: 
            return None
    
    @classmethod
    def __parse_dict(cls,d):
        try : 
            if not isinstance(d,dict):
                raise Exception(f"type {type(d)} Not a dict")
            flat_fict= {}
            stack = [(d, '')]  # Stack holds tuples of (current_dict, current_key)
            while stack:
                c, p = stack.pop()
                
                for k, v in c.items():
                    new_key = f"{p}.{k}" if p else k
                    
                    if isinstance(v, dict):
                        stack.append((v, new_key))  # Push the nested dictionary onto the stack
                    elif isinstance(v, list):
                        for sv in v : 
                            stack.append((sv, new_key))  # Push the nested dictionary onto the stack
                    else:
                        if not cls.__is_skipped(v):
                            if isinstance(v,str):
                                if not cls.__is_skipped(cls.__parse_str(v)):
                                    flat_fict[new_key] = cls.__parse_str(v)
                            else: 
                                flat_fict[new_key] = v  # Add to the flattened dictionary
            return flat_fict if not cls.__is_skipped(flat_fict) else None
        except Exception as e: 
            return None 