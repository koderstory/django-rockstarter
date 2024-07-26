# rockstart/commands.py
import shutil
import os
import subprocess
import getpass
import venv


def create_virtualenv(directory):
    venv_dir = os.path.join(directory, '.venv')
    if not os.path.exists(venv_dir):
        venv.create(venv_dir, with_pip=True)
        print(f"Created virtual environment in {venv_dir}")
    else:
        print(f"Virtual environment already exists in {venv_dir}")

def copy_project_files():
    current_dir = os.path.dirname(__file__)
    template_dir = os.path.join(current_dir, 'src')
    target_dir = os.getcwd()

    try:
        if os.path.exists(template_dir):
            for item in os.listdir(template_dir):
                s = os.path.join(template_dir, item)
                d = os.path.join(target_dir, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)
            print('Project files copied successfully.')
        else:
            print(f"Template directory {template_dir} does not exist.")
    except Exception as e:
        print(f'Error: {e}')


def deploy(domain_name):
    current_user = getpass.getuser()
    current_dir = os.getcwd()

    # Create the virtual environment if it doesn't exist
    create_virtualenv(current_dir)

    # Create the socket file
    socket_content = f"""[Unit]
Description=Socket for {domain_name}
    
[Socket]
ListenStream=/run/{domain_name}.sock
    
[Install]
WantedBy=sockets.target
    """
    
    socket_path = f"/home/dev/{domain_name}.socket"
    # socket_path = f"/etc/systemd/system/{domain_name}.socket"
    with open(socket_path, 'w') as socket_file:
        socket_file.write(socket_content)
    print(f"Created socket file at {socket_path}")

    # Create the service file
    service_content = f"""[Unit]
Description=gunicorn daemon
Requires={domain_name}.socket
After=network.target
    
[Service]
User={current_user}
Group=www-data
WorkingDirectory={current_dir}
ExecStart={current_dir}/.venv/bin/gunicorn \
--access-logfile /var/log/{domain_name}-access.log \
--error-logfile /var/log/{domain_name}-error.log \
--workers 3 \
--bind unix:/run/{domain_name}.sock \
--chdir {current_dir} \
config.wsgi:application
    
[Install]
WantedBy=multi-user.target
    """
        
    service_path = f"/home/dev/{domain_name}.service"
    # service_path = f"/etc/systemd/system/{domain_name}.service"
    with open(service_path, 'w') as service_file:
        service_file.write(service_content)
    print(f"Created service file at {service_path}")

    # Start and enable the service
    # subprocess.run(['sudo', 'systemctl', 'start', domain_name])
    # subprocess.run(['sudo', 'systemctl', 'enable', domain_name])
    print(f"Started and enabled service for {domain_name}")

    # Create the nginx config file
    nginx_content = f"""server {{
        listen 80;
        server_name {domain_name};
        
        location = /favicon.ico {{ access_log off; log_not_found off; }}

        location /static {{
            alias {current_dir}/public/static;
        }}

        location /media {{
            alias {current_dir}/public/media;
        }}

        location / {{
            include proxy_params;
            proxy_pass http://unix:/run/{domain_name}.sock;
        }}
    }}
    """
    nginx_path = f"/home/dev/{domain_name}"
    # nginx_path = f"/etc/nginx/sites-available/{domain_name}"
    with open(nginx_path, 'w') as nginx_file:
        nginx_file.write(nginx_content)
    # if not os.path.exists(f"/etc/nginx/sites-enabled/{domain_name}"):
    #     os.symlink(nginx_path, f"/etc/nginx/sites-enabled/{domain_name}")
    print(f"Created nginx config file at {nginx_path}")

    # Restart nginx to apply the changes
    # subprocess.run(['sudo', 'systemctl', 'restart', 'nginx'])
    print("Restarted nginx")
