###################################################
# Author: Lamoni Finlayson (flamoni@juniper.net)
###################################################
from flask import Flask
from flask import render_template
from pprint import pprint
import json
from flask import request
import time
import ConfigParser
import subprocess
import socket, struct

app = Flask(__name__)

Config = ConfigParser.ConfigParser()
Config.read('/var/www/config.ini')

@app.route('/')
def home():
    return render_template(
        'index.html',
        page_title='Instantiate',
        panel_title='Instantiate'
    )


@app.route('/api/instantiate')
def api_instantiate():

    final = {}

    vCenter_username = request.args.get('vCenter_username')
    vCenter_password = request.args.get('vCenter_password')
    base_name = request.args.get('base_name')
    number_of_devices = int(request.args.get('number_of_devices'))
    start_of_ip_range = request.args.get('start_of_ip_range')
    password_for_srx = request.args.get('password_for_srx')
    space_username = request.args.get('space_username')
    space_password = request.args.get('space_password')
    start_of_telnet_port_range = int(request.args.get('start_of_telnet_port_range'))

    # Convert starting IP address to decimal so we can start incrementing this baby
    packed_ip = socket.inet_aton(start_of_ip_range)
    start_decimal = struct.unpack("!L", packed_ip)[0]
    end_decimal = start_decimal + number_of_devices

    for current_ip_decimal in range(start_decimal, end_decimal):
        current_ip = socket.inet_ntoa(struct.pack('!L', current_ip_decimal))

        cmd = ['/var/www/scripts/instantiate_new_srx.py', '-s=a-inf-vc1', '-u=' + vCenter_username , '-p=' + vCenter_password, '-v=' + base_name + '_' + str(start_of_telnet_port_range), '--template=Mos-BLANK-vSRX', '--datacenter-name=AmerLab', '--cluster-name=Prod_INTEL', '--datastore-name=NetApp-VM-1', '--new-srx-ip=' + current_ip, '--new-srx-root-password=' + password_for_srx, '--new-srx-telnet-port=' + str(start_of_telnet_port_range)]
        # cmd = ['/usr/local/lib/python2.7.10/bin/python', '/var/www/scripts/instantiate_new_srx.py', '-s=192.168.0.17', '-u=' + vCenter_username , '-p=' + vCenter_password, '-v=' + base_name + '_' + str(start_of_telnet_port_range), '--template=VSRX', '--resource-pool=rp1', '--new-srx-ip=' + current_ip, '--new-srx-root-password=' + password_for_srx, '--new-srx-telnet-port=' + str(start_of_telnet_port_range)]

        subprocess.Popen(cmd).wait()

        final[current_ip] = start_of_telnet_port_range

        start_of_telnet_port_range += 1






    #HACKY - I could/should just import the instantiate_new_srx script as a module but... time constraints... for now
    #NOTE - "Mos-BLANK-vSRX" shouldn't be hard-coded, but I'm trying to cut down on the amount of inputs we've got for this demo.
    #NOTE - Pretty much anything that's hardcoded here should either be moved into an html input or to the config file

    return json.dumps(final)





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)