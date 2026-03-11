from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import requests
import os
from redfish import RedfishClient

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# 全局变量用于跟踪扫描进度
scan_progress = {
    'total': 0,
    'scanned': 0,
    'errors': []
}

# 数据库初始化
def init_db():
    conn = sqlite3.connect('hardware.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS servers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  bmc_ip TEXT UNIQUE,
                  username TEXT DEFAULT 'admin',
                  password TEXT DEFAULT 'admin',
                  hostname TEXT,
                  model TEXT,
                  serial_number TEXT,
                  cpu_info TEXT,
                  memory_info TEXT,
                  storage_info TEXT,
                  nic_info TEXT,
                  power_info TEXT,
                  thermal_info TEXT,
                  firmware_info TEXT,
                  log_info TEXT,
                  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('hardware.db')
    c = conn.cursor()
    c.execute('SELECT id, bmc_ip, username, password, hostname, model, serial_number, cpu_info, memory_info, storage_info, nic_info, power_info, thermal_info, firmware_info, log_info, last_updated FROM servers')
    servers = c.fetchall()
    conn.close()
    return render_template('index.html', servers=servers)

@app.route('/import', methods=['GET', 'POST'])
def import_ips():
    if request.method == 'POST':
        default_username = request.form.get('username', 'admin')
        default_password = request.form.get('password', 'admin')
        ips = request.form['ips'].split('\n')
        ips = [ip.strip() for ip in ips if ip.strip()]
        
        for ip_entry in ips:
            # 解析IP地址格式，支持IP或IP,用户名,密码格式
            parts = ip_entry.split(',')
            if len(parts) == 1:
                bmc_ip = parts[0].strip()
                username = default_username
                password = default_password
            elif len(parts) == 3:
                bmc_ip = parts[0].strip()
                username = parts[1].strip()
                password = parts[2].strip()
            else:
                # 格式不正确，跳过
                continue
            
            # 检查IP是否已存在
            conn = sqlite3.connect('hardware.db')
            c = conn.cursor()
            c.execute('SELECT * FROM servers WHERE bmc_ip = ?', (bmc_ip,))
            existing = c.fetchone()
            
            if not existing:
                c.execute('INSERT INTO servers (bmc_ip, username, password) VALUES (?, ?, ?)', (bmc_ip, username, password))
                conn.commit()
            else:
                # 如果IP已存在，更新用户名和密码
                c.execute('UPDATE servers SET username = ?, password = ? WHERE bmc_ip = ?', (username, password, bmc_ip))
                conn.commit()
            conn.close()
        
        flash('IPs imported successfully!')
        return redirect(url_for('index'))
    
    return render_template('import.html')

@app.route('/scan')
def scan_servers():
    global scan_progress
    # 重置进度
    scan_progress = {
        'total': 0,
        'scanned': 0,
        'errors': []
    }
    
    conn = sqlite3.connect('hardware.db')
    c = conn.cursor()
    c.execute('SELECT id, bmc_ip, username, password FROM servers')
    servers = c.fetchall()
    
    scan_progress['total'] = len(servers)
    
    for server_id, bmc_ip, username, password in servers:
        scan_progress['scanned'] += 1
        try:
            # 使用RedfishClient获取硬件信息，使用存储的用户名和密码
            client = RedfishClient(bmc_ip, username, password)
            hardware_info = client.get_all_hardware_info()
            
            c.execute('''UPDATE servers SET 
                        hostname = ?, 
                        model = ?, 
                        serial_number = ?, 
                        cpu_info = ?, 
                        memory_info = ?, 
                        storage_info = ?, 
                        nic_info = ?, 
                        power_info = ?, 
                        thermal_info = ?, 
                        firmware_info = ?, 
                        log_info = ?, 
                        last_updated = CURRENT_TIMESTAMP 
                        WHERE id = ?''', 
                      (hardware_info['hostname'],
                       hardware_info['model'],
                       hardware_info['serial_number'],
                       hardware_info['cpu_info'],
                       hardware_info['memory_info'],
                       hardware_info['storage_info'],
                       hardware_info['nic_info'],
                       hardware_info['power_info'],
                       hardware_info['thermal_info'],
                       hardware_info['firmware_info'],
                       hardware_info['log_info'],
                       server_id))
            conn.commit()
        except Exception as e:
            error_msg = f'{bmc_ip}: {str(e)}'
            scan_progress['errors'].append(error_msg)
            print(f'Error scanning {bmc_ip}: {e}')
    
    conn.close()
    
    # 生成扫描结果消息
    if scan_progress['errors']:
        error_message = '扫描完成，但以下服务器出现错误：\n' + '\n'.join(scan_progress['errors'])
        flash(error_message)
    else:
        flash(f'成功扫描所有 {scan_progress["total"]} 台服务器！')
    
    # 重置进度为完成状态
    scan_progress['scanned'] = scan_progress['total']
    
    return redirect(url_for('index'))

@app.route('/scan_progress')
def get_scan_progress():
    global scan_progress
    return scan_progress

if __name__ == '__main__':
    app.run(debug=True)