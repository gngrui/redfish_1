import requests
import json

class RedfishClient:
    def __init__(self, bmc_ip, username='admin', password='admin'):
        self.bmc_ip = bmc_ip
        self.username = username
        self.password = password
        self.base_url = f'https://{bmc_ip}/redfish/v1'
        self.session = requests.Session()
        self.session.verify = False  # 禁用SSL验证，仅用于测试
        self.session.auth = (username, password)
    
    def get_system_info(self):
        """获取系统基本信息"""
        try:
            response = self.session.get(f'{self.base_url}/Systems/1')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting system info: {e}")
            return None
    
    def get_cpu_info(self):
        """获取CPU信息"""
        try:
            response = self.session.get(f'{self.base_url}/Systems/1/Processors')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting CPU info: {e}")
            return None
    
    def get_memory_info(self):
        """获取内存信息"""
        try:
            response = self.session.get(f'{self.base_url}/Systems/1/Memory')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting memory info: {e}")
            return None
    
    def get_storage_info(self):
        """获取存储信息"""
        try:
            response = self.session.get(f'{self.base_url}/Systems/1/Storage')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting storage info: {e}")
            return None
    
    def get_nic_info(self):
        """获取网卡信息"""
        try:
            response = self.session.get(f'{self.base_url}/Chassis/1/NetworkAdapters')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting NIC info: {e}")
            return None
    
    def get_power_info(self):
        """获取电源信息"""
        try:
            response = self.session.get(f'{self.base_url}/Chassis/1/Power')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting power info: {e}")
            return None
    
    def get_thermal_info(self):
        """获取温度和风扇信息"""
        try:
            response = self.session.get(f'{self.base_url}/Chassis/1/Thermal')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting thermal info: {e}")
            return None
    
    def get_firmware_info(self):
        """获取固件信息"""
        try:
            response = self.session.get(f'{self.base_url}/UpdateService')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting firmware info: {e}")
            return None
    
    def get_log_info(self):
        """获取系统日志信息"""
        try:
            response = self.session.get(f'{self.base_url}/Managers/1/LogServices')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting log info: {e}")
            return None
    
    def get_all_hardware_info(self):
        """获取所有硬件信息"""
        system_info = self.get_system_info()
        cpu_info = self.get_cpu_info()
        memory_info = self.get_memory_info()
        storage_info = self.get_storage_info()
        nic_info = self.get_nic_info()
        power_info = self.get_power_info()
        thermal_info = self.get_thermal_info()
        firmware_info = self.get_firmware_info()
        log_info = self.get_log_info()
        
        hardware_info = {
            'hostname': system_info.get('HostName', '') if system_info else '',
            'model': system_info.get('Model', '') if system_info else '',
            'serial_number': system_info.get('SerialNumber', '') if system_info else '',
            'cpu_info': self._format_cpu_info(cpu_info),
            'memory_info': self._format_memory_info(memory_info),
            'storage_info': self._format_storage_info(storage_info),
            'nic_info': self._format_nic_info(nic_info),
            'power_info': self._format_power_info(power_info),
            'thermal_info': self._format_thermal_info(thermal_info),
            'firmware_info': self._format_firmware_info(firmware_info),
            'log_info': self._format_log_info(log_info)
        }
        
        return hardware_info
    
    def _format_cpu_info(self, cpu_info):
        """格式化CPU信息"""
        if not cpu_info or 'Members' not in cpu_info:
            return 'Unknown'
        
        cpus = []
        for cpu in cpu_info['Members']:
            try:
                response = self.session.get(cpu['@odata.id'])
                response.raise_for_status()
                cpu_detail = response.json()
                cpus.append(f"{cpu_detail.get('Model', 'Unknown')} ({cpu_detail.get('TotalCores', 'Unknown')} cores)")
            except:
                pass
        
        return ', '.join(cpus) if cpus else 'Unknown'
    
    def _format_memory_info(self, memory_info):
        """格式化内存信息"""
        if not memory_info or 'Members' not in memory_info:
            return 'Unknown'
        
        total_memory = 0
        for mem in memory_info['Members']:
            try:
                response = self.session.get(mem['@odata.id'])
                response.raise_for_status()
                mem_detail = response.json()
                total_memory += mem_detail.get('CapacityMiB', 0)
            except:
                pass
        
        return f"{total_memory // 1024}GB"
    
    def _format_storage_info(self, storage_info):
        """格式化存储信息"""
        if not storage_info or 'Members' not in storage_info:
            return 'Unknown'
        
        storages = []
        for storage in storage_info['Members']:
            try:
                response = self.session.get(storage['@odata.id'])
                response.raise_for_status()
                storage_detail = response.json()
                
                if 'Drives' in storage_detail:
                    drive_count = len(storage_detail['Drives'])
                    storages.append(f"{storage_detail.get('Name', 'Unknown')} ({drive_count} drives)")
            except:
                pass
        
        return ', '.join(storages) if storages else 'Unknown'
    
    def _format_nic_info(self, nic_info):
        """格式化网卡信息"""
        if not nic_info or 'Members' not in nic_info:
            return 'Unknown'
        
        nics = []
        for nic in nic_info['Members']:
            try:
                response = self.session.get(nic['@odata.id'])
                response.raise_for_status()
                nic_detail = response.json()
                nics.append(nic_detail.get('Model', 'Unknown'))
            except:
                pass
        
        return ', '.join(nics) if nics else 'Unknown'
    
    def _format_power_info(self, power_info):
        """格式化电源信息"""
        if not power_info:
            return 'Unknown'
        
        power_supplies = []
        if 'PowerSupplies' in power_info:
            for ps in power_info['PowerSupplies']:
                if 'Model' in ps and 'Status' in ps and 'State' in ps['Status']:
                    power_supplies.append(f"{ps['Model']} ({ps['Status']['State']})")
        
        return ', '.join(power_supplies) if power_supplies else 'Unknown'
    
    def _format_thermal_info(self, thermal_info):
        """格式化温度和风扇信息"""
        if not thermal_info:
            return 'Unknown'
        
        thermal_details = []
        
        # 处理风扇信息
        if 'Fans' in thermal_info:
            fan_count = len(thermal_info['Fans'])
            thermal_details.append(f"{fan_count} fans")
        
        # 处理温度传感器信息
        if 'Temperatures' in thermal_info:
            temp_count = len(thermal_info['Temperatures'])
            thermal_details.append(f"{temp_count} temperature sensors")
        
        return ', '.join(thermal_details) if thermal_details else 'Unknown'
    
    def _format_firmware_info(self, firmware_info):
        """格式化固件信息"""
        if not firmware_info:
            return 'Unknown'
        
        firmware_details = []
        if 'FirmwareInventory' in firmware_info:
            for fw in firmware_info['FirmwareInventory']:
                if 'Name' in fw and 'Version' in fw:
                    firmware_details.append(f"{fw['Name']}: {fw['Version']}")
        
        return ', '.join(firmware_details) if firmware_details else 'Unknown'
    
    def _format_log_info(self, log_info):
        """格式化系统日志信息"""
        if not log_info or 'Members' not in log_info:
            return 'Unknown'
        
        logs = []
        for log in log_info['Members']:
            try:
                response = self.session.get(log['@odata.id'])
                response.raise_for_status()
                log_detail = response.json()
                if 'Name' in log_detail and 'Entries' in log_detail and 'Members' in log_detail['Entries']:
                    entry_count = len(log_detail['Entries']['Members'])
                    logs.append(f"{log_detail['Name']}: {entry_count} entries")
            except:
                pass
        
        return ', '.join(logs) if logs else 'Unknown'