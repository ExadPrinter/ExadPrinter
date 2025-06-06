
import re
from datetime import datetime, timedelta
import jc

class ShellAttributeParser:
    SHELL_ATTRIBUTES = [
        "cpu_information", "memory_information", "device_tree", "storage_information",
        "acpi_battery", "nproc", "lsmod", "lspci", "lsusb", "system_root_structure",
        "system_typefaces", "ringtones_list", "ringtones_list_ext", "df",
        "kernel_information", "distribution_information", "system_uptime",
        "sysctl", "system_conf_vars", "installed_packages", "running_processes",
        "user_accounts", "groups", "hostname", "hwclock", "tty", "ssty_active",
        "dmesg_first_1000_lines", "dmesg_last_1000_lines", "authentication_logs",
        "arp_cache", "dumpsys", "meminfo", "cpuinfo", "system_logs", "getprop_net_dns1",
        "getprop_net_dns2", "getprop_net_dns3", "getprop_net_dns4","getprop", "netstat", 
        "network_interfaces", "routing_table", "routing_table_n"
    ]
    # Ignored attributes, means that we don't parse them, we just check if there is no error when execution and return 1
    # 1 : Means that the command executed without errors 
    IGNORED_SHELL_ATTRIBUTES = ["cpu_information", "device_tree", "storage_information",
    "lsmod", "lspci", "lsusb", "distribution_information", "sysctl", "system_conf_vars", "installed_packages",
    "running_processes","hwclock", "tty", "ssty_active", "authentication_logs", "routing_table", "routing_table_n"]

    LISTING_SHELL_ATTRIBUTES = ["system_root_structure", "system_typefaces", "ringtones_list", "ringtones_list_ext"]
    
    @classmethod
    def isShellAttribute(cls,key): 
        """
        Check if attribute is shell attribute
        """
        return key in cls.SHELL_ATTRIBUTES
    
    @classmethod
    def parse(cls,key,value,timestamp=None): 
        try:
            # Skip parsing if it's not considered
            if not cls.isShellAttribute(key):
                return None
            elif cls.__is_skipped(value):
                return None
            elif key in cls.IGNORED_SHELL_ATTRIBUTES:
                # Command executable on the device 
                return 1
            elif key in cls.LISTING_SHELL_ATTRIBUTES: 
                return cls.__parse_list(value)
            elif key == "system_uptime":
                return cls.__parse_uptime(value[0],timestamp)
            elif key == "memory_information": 
                return cls.__parse_free(value)
            elif key == "meminfo": 
                return cls.__parse_meminfo(value)
            elif key == "cpuinfo": 
                return cls.__parse_cpuinfo(value)
            elif key == "getprop": 
                return cls.__parse_getprop(value)
            elif key == "acpi_battery":
                return cls.__parse_acpi_battery(value)
            elif key == "df": 
                return cls.__parse_df(value)
            elif key in ["dmesg_first_1000_lines","dmesg_last_1000_lines","system_logs"]:
                return cls.__parse_dmesg(value)
            elif key == "network_interfaces": 
                return cls.__parse_network_interfaces(value)
            elif key == "netstat":
                return cls.__parse_netstat(value)
            elif key == "dumpsys": 
                return cls.__parse_dumpsys(value)
            elif len(value) == 1: 
                return int(value[0]) if value[0].isdigit() else value[0].strip()
            else: 
                return value
        except:
            return None
    @staticmethod
    def __is_skipped(value):
        SKIPPED = ["MNC", "FNC", "NULL","UNDEFINED"]
        if value == None:
            return True
        elif isinstance(value, list):
            return all(not line or line in SKIPPED for line in value)
        else:
            return False
    
    # Keep only totals 
    @staticmethod
    def __parse_free(list):
        list_parsed = jc.parse("free", '\n'.join(list))
        result = {}
        for item in list_parsed:
            if "type" in item and item["type"] in ["Mem", "Swap"]:
                if "total" in item:
                    result[f"{item["type"]}Total"] = item["total"]
        return result
    
    @staticmethod
    def __parse_meminfo(list):
        list_parsed = jc.parse("proc-meminfo", '\n'.join(list))
        result = {}
   
        if "MemTotal" in list_parsed:
                result["MemTotal"] = list_parsed["MemTotal"]
        if "SwapTotal" in list_parsed:
            result["SwapTotal"] = list_parsed["SwapTotal"]
        return result

    @staticmethod
    def __parse_cpuinfo(_list):
        list_parsed = jc.parse("proc-cpuinfo", '\n'.join(_list))
        result = {
            "nproc": len(list_parsed)
        }
        for proc in list_parsed:
            for key,value in proc.items(): 
                if key == "processor":
                    continue
                if key not in result:
                    result[key] = set()
                result[key].add(value)
        for key, value in result.items(): 
            if key == "nproc":
                continue
            if len(value) == 1:
                result[key] = list(value)[0]
            else : 
                result[key] = str(list(value))
        return result
    @staticmethod
    def __parse_dumpsys(dumpsys_list):
        """
        Parse the dumpsys output and keep only currently running services
        """
        currently_running_services=[]
        for line in dumpsys_list:
            if line ==  "Currently running services:":
                continue
            if all(char == '-' for char in line):
                break
            else:
                # Add values to the current key
                currently_running_services.append(line.strip()) 
        
        return currently_running_services 
    
    # Keep only ip @  
    @staticmethod
    def __parse_netstat(netstat_list):
        active_networks_list = []
        for line in netstat_list : 
            if line == "Active UNIX domain sockets (w/o servers)":
                break 
            active_networks_list.append(line)
        netstat_parsed = jc.parse("netstat", '\n'.join(active_networks_list))
        active_netwrok_parsed = set()
        for item in netstat_parsed: 
            if "local_address" in item: 
                active_netwrok_parsed.add(netstat_parsed["local_address"])
        return list(active_netwrok_parsed)
    
    # Keep only ip @ 
    @staticmethod
    def __parse_network_interfaces(network_list):
        network_list_parsed = jc.parse("ifconfig", '\n'.join(network_list))
        network_object = set()
        for item in network_list_parsed:
            if isinstance(item, dict): 
                name = item.get("name", "")
                ip = item.get("ipv4_addr", "")
                if name and name.lower() != "lo" and ip:
                    network_object.add(ip)
        return list(network_object)
    
    @staticmethod
    def __parse_dmesg(dmesg_list):
        """
        Extracts relevant system and personal information from dmesg output.
        Returns a dictionary of detected information.
        """
        extracted_info = []
        
        # Regex patterns for various info
        patterns = {
            "kernel_version": re.compile(r"Linux version ([\d+.]+)", re.IGNORECASE),
            "compiled_by": re.compile(r"\(([^@)]+@[^)]+)\)", re.IGNORECASE),
            "compiler": re.compile(r"gcc version ([\d+.x]+)", re.IGNORECASE),
            "build_date": re.compile(r"#\d+ SMP PREEMPT (.+)", re.IGNORECASE),
            "command_line": re.compile(r"Command line: (.+)", re.IGNORECASE),
            "hypervisor": re.compile(r"Hypervisor detected: (\w+)", re.IGNORECASE),
            "product": re.compile(r"Product: ([\w\s]+)", re.IGNORECASE),
            "manufacturer": re.compile(r"Manufacturer: ([\w\s]+)", re.IGNORECASE),
        }
        
        capturing_cpus = False
        
        i = 0
        while i < len(dmesg_list):
            parts = dmesg_list[i].split("] ",2)
            if len(parts) == 2: 
                line = parts[1].strip()
                if "KERNEL supported cpus" in line:
                    capturing_cpus = True
                    i += 1 
                    continue
                if capturing_cpus:
                    if re.search(r'[:\d\-_+]', line):  # Stop capturing cpus if special character or number found
                        capturing_cpus = False
                    else: 
                        if line not in extracted_info:
                            extracted_info.append(line)
                    i += 1 
                    continue
                else: 
                    for key, pattern in patterns.items():
                        matches = pattern.findall(line)
                        for match in matches:
                            item = match.strip()
                            if item not in extracted_info:
                                extracted_info.append(item)
            i += 1
        return extracted_info
    @staticmethod
    def __parse_df(df_list):
        df_list_parsed = jc.parse("df", '\n'.join(df_list))
        result = []
        for item in df_list_parsed:
            if isinstance(item, dict): 
                filesystem = item.get("filesystem", "")
                mounted_on = item.get("filesystem", "")
                line = ' '.join([filesystem,mounted_on])
                if line not in result: 
                    result.append(line)
        return result
    @staticmethod  
    def __parse_list(list):
        result = []
        
        # Process each line in the list
        for item in list:
            # Skip empty lines
            if not item.strip():
                continue
            
            if item.lower().startswith("total"):
                #result.append(item)
                continue
            else:
                # Parse the line using regex
                match = re.match(r'(.*)\s+(\d+)\s+(\w+)\s+(\w+)\s+(\d+)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s+(.+)', item)
                if match:
                    _, _, _, _, _, date, name = match.groups()
                    # Check for symbolic link
                    #result.append(' '.join([date,name]))  
                    result.append(name)     
        return result
    @staticmethod
    def __parse_acpi_battery(acpi_list):
        acpi_object = []
        for item in acpi_list: 
            parts = item.split(":")
            if len(parts)>1 :
                types = ["cooling", "thermal", "adapter", "battery"]
                key = next((type for type in types if type in parts[0].lower()), "")  
                value = parts[1].strip().split(" ")[0]
                if key:
                    line = ' '.join([key,value])
                    if line not in acpi_object :    
                        acpi_object.append(line)
        return acpi_object
    @staticmethod 
    def __parse_getprop(prop_list):
        parsed_data = {}
        for prop in prop_list:
            match = re.match(r'\[(.+?)\]: \[(.+?)\]', prop)
            if match:
                key, value = match.groups()
                if ',' in value:
                    values = value.split(',')
                    converted_values = []
                    for item in values:
                        item = item.strip()
                        converted_values.append(int(item) if item.isdigit() else item)
                    value = converted_values 
                else: 
                    parsed_data[key] = int(value) if value.isdigit() else value
        return parsed_data
    @staticmethod
    def __parse_uptime(uptime_string, unix_timestamp):
        """
        Parses the uptime string and computes the last reboot date.
        Returns: last_reboot date '%Y-%m-%d %H:%M'
        """
        if unix_timestamp > 10**10:  # Convert ms to seconds if needed
            unix_timestamp //= 1000
        # Extract exact execution time from uptime string
        h, m, s = map(int, uptime_string.split(' up ')[0].split(':'))
        execution_date = datetime.fromtimestamp(unix_timestamp).replace(hour=h, minute=m, second=s)
        # Extract uptime duration
        uptime_match = re.search(r'up\s+((\d+)\s+days?,\s+)?(\d+)?:?(\d+)\s*(min|hours?)?', uptime_string)
        if not uptime_match:
            raise ValueError("Could not parse uptime string")
        
        days = int(uptime_match.group(2) or 0)
        hours = int(uptime_match.group(3) or 0)
        minutes = int(uptime_match.group(4) or 0)
        unit = uptime_match.group(5)  # Determine if time is in minutes/hours
        
        if unit == "min":
            hours = 0  # Ensure no misinterpretation
        elif unit in ("hour", "hours"):
            minutes = 0  # Ensure no misinterpretation
        
        # Compute last reboot datetime
        uptime_duration = timedelta(days=days, hours=hours, minutes=minutes)
        last_reboot = execution_date - uptime_duration
        
        return last_reboot.strftime('%Y-%m-%d %H:%M')