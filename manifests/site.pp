# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# == Define: nova-bugs
#
define nova-bugs::site(
  $gerrit_url = '',
  $gerrit_port = '',
  $gerrit_user = '',
  $nova-bugs_rsa_key_contents = '',
  $nova-bugs_rsa_pubkey_contents = '',
  $nova-bugs_gerrit_ssh_key = '',
  $git_url = '',
  $httproot = '',
  $serveradmin = ''
) {

  file { '/var/lib/nova-bugs/.ssh/':
    ensure  => directory,
    owner   => 'nova-bugs',
    group   => 'nova-bugs',
    mode    => '0700',
    require => User['nova-bugs'],
  }

  if $nova-bugs_rsa_key_contents != '' {
    file { '/var/lib/nova-bugs/.ssh/id_rsa':
      owner   => 'nova-bugs',
      group   => 'nova-bugs',
      mode    => '0600',
      content => $nova-bugs_rsa_key_contents,
      replace => true,
      require => File['/var/lib/nova-bugs/.ssh/']
    }
  }

  if $nova-bugs_rsa_pubkey_contents != '' {
    file { '/var/lib/nova-bugs/.ssh/id_rsa.pub':
      owner   => 'nova-bugs',
      group   => 'nova-bugs',
      mode    => '0600',
      content => nova-bugs,
      replace => true,
      require => File['/var/lib/nova-bugs/.ssh/']
    }
  }

  if $nova-bugs_gerrit_ssh_key != '' {
    file { '/var/lib/nova-bugs/.ssh/known_hosts':
      owner   => 'nova-bugs',
      group   => 'nova-bugs',
      mode    => '0600',
      content => "${gerrit_url} ${nova-bugs_gerrit_ssh_key}",
      replace => true,
      require => File['/var/lib/nova-bugs/.ssh/']
    }
  }

  file {'/var/lib/nova-bugs/nova-bugs':
    ensure  => directory,
    owner   => 'nova-bugs',
    group   => 'nova-bugs',
    mode    => '0755',
    require => File['/var/lib/nova-bugs/'],
  }

  vcsrepo { '/var/lib/nova-bugs/nova-bugs':
    ensure   => latest,
    provider => git,
    source   => $git_url,
    revision => 'master',
  }

  file { $httproot:
    ensure => directory,
    owner  => 'nova-bugs',
    group  => 'nova-bugs',
    mode   => '0755',
  }

  file { '/var/lib/nova-bugs/.ssh/config':
    ensure   => present,
    content  => template('nova-bugs/ssh_config.erb'),
    owner    => 'nova-bugs',
    group    => 'nova-bugs',
    mode     => '0644',
  }

  cron { 'update nova-bugs':
    command => "cd /var/lib/nova-bugs/nova-bugs && PYTHONPATH=\$PWD flock -n /var/lib/nova-bugs/update.lock python bin/nova-bugs -o ${httproot}",
    minute  => '*/30',
    user    => 'nova-bugs',
  }

}

# vim:sw=2:ts=2:expandtab:textwidth=79