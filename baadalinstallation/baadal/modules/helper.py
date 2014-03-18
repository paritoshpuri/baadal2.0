# -*- coding: utf-8 -*-
###################################################################################

import os, re, random
from gluon import current
from gluon.validators import Validator
import logging

def is_moderator():
    if current.ADMIN in current.auth.user_groups.values():
        return True
    return False    

def is_faculty():
    if current.FACULTY in current.auth.user_groups.values():
        return True
    return False 
    
def is_orgadmin():
    if current.ORGADMIN in current.auth.user_groups.values():
        return True
    return False        

def get_config_file():

    import ConfigParser    
    config = ConfigParser.ConfigParser()
    config.read(os.path.join(get_context_path(), 'static/baadalapp.cfg'));
    return config

def get_context_path():

    ctx_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
    return ctx_path

def get_datetime():
    import datetime
    return datetime.datetime.now()

# Get value from table 'costants'
def get_constant(constant_name):
    constant = current.db.constants(name = constant_name)['value']
    return constant

# Update value into table 'costants'
def update_constant(constant_name, constant_value):
    current.db(current.db.constants.name == constant_name).update(value = constant_value)
    return 

#Executes command on remote machine using paramiko SSHClient
def execute_remote_cmd(machine_ip, user_name, command, password=None):

    logger.debug("executing remote command %s on %s:"  %(command, machine_ip))

    output = None
    try:
        import paramiko
    
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(machine_ip, username = user_name, password = password)
        stdin,stdout,stderr = ssh.exec_command(command)  # @UnusedVariable
        
        output = "".join(stdout.readlines())
        error = "".join(stderr.readlines())
        if (stdout.channel.recv_exit_status()) == 1:
            raise Exception("Exception while executing remote command %s on %s: %s" %(command, machine_ip, error))
    except paramiko.SSHException:
        log_exception()
        raise
    finally:
        if ssh:
            ssh.close()
    
    return output

#Checks if string represents 4 octets seperated by decimal.
def is_valid_ipv4(value):
    regex = re.compile(
        '^(([1-9]?\d|1\d\d|2[0-4]\d|25[0-5])\.){3}([1-9]?\d|1\d\d|2[0-4]\d|25[0-5])$')
    return regex.match(value)

#Validates each IP string, checks if first three octets are same; and the last octet has a valid range.
def validate_ip_range(ipFrom, ipTo):
    
    if is_valid_ipv4(ipFrom) and is_valid_ipv4(ipTo):
        ip1 = ipFrom.split('.')
        ip2 = ipTo.split('.')
        if ip1[0] == ip2[0] and ip1[1] == ip2[1] and ip1[2] == ip2[2] and int(ip1[3]) < int(ip2[3]):
            return True
    return False

#Get List of IPs in a validated IP range
def get_ips_in_range(ipFrom, ipTo):
    
    ip_addr_lst = []
    ip1 = ipFrom.split('.')
    ip2 = ipTo.split('.')
    idx =  - (len(ip1[3]))
    subnet = str(ipFrom[:idx])
    for x in range(int(ip1[3]), int(ip2[3])+1):
        ip_addr_lst.append(subnet + str(x))
    return ip_addr_lst


# Generates MAC address
def generate_random_mac():
    MAC_GEN_FIRST_BIT=0xa2
    MAC_GEN_FIXED_BITS=3
    
    mac = [MAC_GEN_FIRST_BIT]
    i = 1
    while i <  MAC_GEN_FIXED_BITS:
        mac.append(0x00)
        i += 1
    while i <  6:    
        mac.append(random.randint(0x00, 0xff))
        i += 1
    return (':'.join(map(lambda x: "%02x" % x, mac))).upper()
    
def check_db_storage_type():
    config = get_config_file()
    auth_type = config.get("AUTH_CONF","auth_type")
    if auth_type == current.AUTH_TYPE_DB:
        return True
    return False
    
#Creates bulk entry into DHCP
# Gets list of tuple containing (host_name, mac_addr, ip_addr)
def create_dhcp_bulk_entry(dhcp_info_list):
    
    config = get_config_file()
    dhcp_ip = config.get("GENERAL_CONF","dhcp_ip")
    entry_cmd = "echo -e  '"
    for dhcp_info in dhcp_info_list:
        entry_cmd += "host %s {\n\thardware ethernet %s;\n\tfixed-address %s;\n}\n" %(dhcp_info[0], dhcp_info[1], dhcp_info[2])
    entry_cmd += "' >> /etc/dhcp/dhcpd.conf"    
    restart_cmd = "/etc/init.d/isc-dhcp-server restart"

    execute_remote_cmd(dhcp_ip, 'root', entry_cmd)
    execute_remote_cmd(dhcp_ip, 'root', restart_cmd)

#Creates single entry into DHCP
def create_dhcp_entry(host_name, mac_addr, ip_addr):
    
    dhcp_info_list = [(host_name, mac_addr, ip_addr)]
    create_dhcp_bulk_entry(dhcp_info_list)

#Removes entry from DHCP
def remove_dhcp_entry(host_name, mac_addr, ip_addr):
    config = get_config_file()
    dhcp_ip = config.get("GENERAL_CONF","dhcp_ip")
    entry_cmd = "sed -i '/host.*%s.*{/ {N;N;N; s/host.*%s.*{.*hardware.*ethernet.*%s;.*fixed-address.*%s;.*}//g}' /etc/dhcp/dhcpd.conf" %(host_name, host_name, mac_addr, ip_addr)
    restart_cmd = "/etc/init.d/isc-dhcp-server restart"
    
    execute_remote_cmd(dhcp_ip, 'root', entry_cmd)
    execute_remote_cmd(dhcp_ip, 'root', restart_cmd)


def get_configured_logger(name):
    logger = logging.getLogger(name)
    if (len(logger.handlers) == 0):
        # This logger has no handlers, so we can assume it hasn't yet been configured.
        log_file = os.path.join(current.request.folder,'logs/%s.log'%(name)) # @UndefinedVariable
        handler = logging.handlers.TimedRotatingFileHandler(log_file, when='midnight', interval=1, backupCount=14)

        formatter="%(asctime)s %(levelname)s %(funcName)s():%(lineno)d %(message)s"
        handler.setFormatter(logging.Formatter(formatter))
        handler.setLevel(logging.DEBUG)
        
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

    return logger

logger = get_configured_logger(current.request.application)  # @UndefinedVariable

def log_exception(message=None):
    import sys, traceback
    etype, value, tb = sys.exc_info()
    trace = ''.join(traceback.format_exception(etype, value, tb, 10))
    if message:
        trace = message + trace
    logger.error(trace)
    return trace


class IS_MAC_ADDRESS(Validator):
    
    regex = re.compile('^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    
    def __init__(self, error_message='enter valid MAC address'):
        self.error_message = error_message

    def __call__(self, value):
        if self.regex.match(value):
            return (value, None)
        else:
            return (value, self.error_message)

