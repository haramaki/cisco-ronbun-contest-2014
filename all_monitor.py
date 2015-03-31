import json
import requests
from nova.compute import monitors


class APICController(object):
    def __init__(self, apic_ip):
        self.base_url = 'https://%s/api' % (apic_ip)

    def login(self, name, pwd):
        name_pwd = json.dumps(
            {'aaaUser': {'attributes': {'name': name, 'pwd': pwd}}})
        login_url = '%s/aaaLogin.json' % (self.base_url)
        # need login error handling
        post_response = requests.post(login_url, data=name_pwd, verify=False)
        # get token from login response structure
        auth = json.loads(post_response.text)
        login_attributes = auth['imdata'][0]['aaaLogin']['attributes']
        return login_attributes['token']

    def get_port_health(self, auth_token, switch):
        cookies = {}
        # set cookie
        cookies['APIC-cookie'] = auth_token
        # create health score URI
        request_url = '%s/mo/topology' % self.base_url
        if 'pod' in switch:
            request_url = '%s/pod-%s' % (request_url, switch['pod'])
        if 'node' in switch:
            request_url = '%s/node-%s' % (request_url, switch['node'])
        if 'slot' in switch:
            request_url = '%s/sys/ch/lcslot-%s' % (request_url, switch['slot'])
        if 'port' in switch:
            request_url = '%s/lc/leafport-%s' % (request_url, switch['port'])
        request_url = '%s/health.json' % request_url
        get_response = requests.get(request_url, cookies=cookies, verify=False)
        # return json data
        return get_response.json()


class MyDriver(object):
    # Example driver to get Leaf switch health
    def get_metric_score(self, **kwargs):
        apic_info = {'ip': 'IPADDRESS', 'user': 'ADMIN', 'pwd': 'PASSWORD'}
        switch = {'pod': '1', 'node': '101', 'slot': '1', 'port': '1'}
        apic = APICController(apic_info['ip'])
        token = apic.login(apic_info['user'], apic_info['pwd'])
        json_data = apic.get_port_health(token, switch)
        score = json_data["imdata"][0]["healthInst"]["attributes"]["twScore"]
        # return health score as a floating value
        return float(score)


class MetricMonitor(monitors.ResourceMonitorBase):

    def __init__(self, parent):
        super(MetricMonitor, self).__init__(parent)
        self.source = "APIC"
        self.mdriver = MyDriver()

    def _get_metric_score(self, **kwargs):
        # Return health score and its timestamps.
        return self.mdriver.get_metric_score(), None
