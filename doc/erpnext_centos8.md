# Install ERPNext on CentOS 8

Some quick notes on installing ERPNext on CentOS 8.

Just so you know:

 * This is a minimal working installation.

 * We don't cover making the box secure - that's up to you!

## Install CentOS8.

1) Install CentOS 8. We chose the "minimal" install for this guide.

2) After install, login and ensure your installation is up to date
   by running :

```sh
  sudo yum update -y
```

3) Install the extra packages repository:

```sh
  sudo yum install -y epel-release
```

## Prepare OS for ERPNext

1) Install required packages:

```sh
  sudo yum install -y gcc make git mariadb mariadb-server nginx supervisor python3 python3-devel python2 python2-devel redis nodejs
  sudo npm install -g yarn
```

2) Create a user for ERPNext to run as, allowing it sudo access too:

```sh
  sudo useradd -m erp -G wheel
```

3) (Optional) Configure sudo so it doesn't need a password:

This step is optional but it might save you quite a bit of typing.
You might want to cut'n'paste this one!

```sh
  sudo sed -i 's/^#\s*\(%wheel\s\+ALL=(ALL)\s\+NOPASSWD:\s\+ALL\)/\1/' /etc/sudoers
```

4) Open the firewall:

```sh
  sudo firewall-cmd --zone=public --add-port=80/tcp
  sudo firewall-cmd --zone=public --add-port=443/tcp
  sudo firewall-cmd --zone=public --add-port=8000/tcp
  sudo firewall-cmd --runtime-to-permanent
```

5) Set some kernel parameters:

```sh
  echo "vm.overcommit_memory = 1" | sudo tee -a /etc/sysctl.conf
  echo "echo never > /sys/kernel/mm/transparent_hugepage/enabled" | sudo tee -a /etc/rc.d/rc.local
  sudo chmod 755 /etc/rc.d/rc.local 
```

6) Reboot:

This will allow the updates to settle and the kernel parameters to get set.

```sh
  sudo reboot
```

## Prepare MariaDB (mysql) for ERPNext

1) Edit the MariaDB configuration to set the correct character set:

```sh
  cat <<EOF >/etc/my.cnf.d/erpnext.cnf
[mysqld]
innodb-file-format=barracuda
innodb-file-per-table=1
innodb-large-prefix=1
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
EOF
```

2) Enable and start the MariaDB service:

```sh
  systemctl enable mariadb
  systemctl start mariadb
```

3) Secure the service:

Start the secure script:

```sh
  mysql_secure_installation
```

This is an interactive script that will ask you questions.

Options are:
  * Current root password is none - just press enter.
  * Enter a new password for the root password - remember it!
  * Remove anonymous users - Y
  * Disallow remote root - Y
  * Remove test database - Y
  * Reload priv tables now - Y

Done!

## Install ERPNext

1) Switch to the ERP user (or login as it) and change to home directory:

```sh
  su erp
  cd
```

2) Install frappe-bench with pip and initialise:

This step takes a while so get yourself a beer. It reaches out to the Internet
and downloads a bunch of stuff and then builds it.

```sh
  pip3 install --user frappe-bench
  bench init frappe-bench --frappe-branch version-12
```

For the second command, a red error message appears early on about an "editable
requirement." Ignore it.

When it's done you should get the message in green text:

```
  SUCCESS: Bench frappe-bench initialized
```

3) Create a new frappe site:

Prerequisites:
  * You need a name for your site. We called ours erpdev.softwaretohardware.com
  * You'll need your MariaDB root password from earlier.

First we temporarily start the frappe development server:

```sh
  cd frappe-bench
  sed -i '/web:/ s/$/ --noreload/' Procfile
  bench start >/tmp/bench_log &
```

Then we create a new site. Substitute your own name.

```sh
  bench new-site erpdev.softwaretohardware.com
```

You will be prompted for the mysql password and a bit later, for the
adminstrator password for your new site.

NOTE: Don't visit your new site with a browser just yet!

4) Install the ERPNext application

```sh
  bench get-app erpnext --branch version-12
  bench install-app erpnext
```

At the end of this step, the temporary server will stop and the exception
message looks bad. You can ignore it.

5) Bring back your temporary server

```sh
  bench start >/tmp/bench_log &
  bench update
```

You now have an ERPNext instance listening on port 8000.

Visit it with a browser to set it up.

When you're done, bring the server to the foreground and press Ctrl+C

```sh
  fg
```

You can start it again at any time.

## (Optional) Setup in production mode

Ensure the test server from above is not running.


1) Create the production configuration files for supervisor and nginx:

```sh
  bench setup supervisor
  bench setup nginx
```

2) Set permissions including relaxing SELinux a bit

```sh
  chmod 755 /home/erp
  chcon -t httpd_config_t config/nginx.conf
  sudo setsebool -P httpd_can_network_connect=1
  sudo setsebool -P httpd_enable_homedirs=1
  sudo setsebool -P httpd_read_user_content=1
```

3) Link the new configuration files to their respective services:

```sh
  sudo ln -s `pwd`/config/supervisor.conf /etc/supervisord.d/frappe-bench.ini
  sudo ln -s `pwd`/config/nginx.conf /etc/nginx/conf.d/frappe-bench.conf
```

4) Enable services to start at boot:
```sh
  sudo systemctl enable supervisord
  sudo systemctl enable nginx
```

5) Reboot:
```sh
  sudo reboot
```

After this your server should be accessible on port 80. You'll need to use the domain name you specified above when creating the site, otherwise you'll see the default nginx page.
