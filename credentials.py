# -*- coding: utf-8 -*-

from keystoneclient import auth as ks_auth
from keystoneclient import session as ks_session
from oslo_config import cfg

TGROUP = cfg.OptGroup(name="nova")

OPTS = [
    cfg.StrOpt('username'),
    cfg.StrOpt('password'),
    cfg.StrOpt('auth_url'),
    cfg.StrOpt('project_name'),
]

CFG = cfg.CONF
CFG.register_opts(OPTS, TGROUP)

def get_q_creds():
    d = {}
    d['username'] = CFG.nova.username
    d['password'] = CFG.nova.password
    d['auth_url'] = CFG.nova.auth_url + '/v2.0'
    d['tenant_name'] = CFG.nova.project_name
    return d

def get_n_creds():
    d = {}
    d['username'] = CFG.nova.username
    d['api_key'] = CFG.nova.password
    d['auth_url'] = CFG.nova.auth_url + '/v2.0'
    d['project_id'] = CFG.nova.project_name
    return d

def get_c_creds():
    d = {}
    d['os_username'] = CFG.nova.username
    d['os_password'] = CFG.nova.password
    d['os_auth_url'] = CFG.nova.auth_url
    d['os_tenant_name'] = CFG.nova.project_name
    return d

def get_session():
    auth = ks_auth.load_from_conf_options(cfg.CONF, 'nova')
    session = ks_session.Session.load_from_conf_options(cfg.CONF,
                                                        'nova',
                                                        auth=auth)
    return session
