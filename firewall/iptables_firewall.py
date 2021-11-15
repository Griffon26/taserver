from ipaddress import ip_address
import ipaddress
from logging import Logger
import logging
import subprocess
from typing import List, NamedTuple

from gevent.queue import Queue

from common.logging import set_up_logging
from common.ports import Ports


class Rule(NamedTuple):
  protocol: str = None
  ports: List[str] = None
  target: str = None
  ip_address: str = None


class IPTables:

  def __init__(self, logger: Logger):
    self.logger = logger

  def iptables(self, command: str, chain: str, rule: Rule = Rule(), quiet: bool = False) -> int:
    args = ['iptables', '-w', command, chain]

    if rule.protocol:
      args += ['-p', rule.protocol]
    
    if rule.ports is not None:
      if len(rule.ports) == 1:
        args += ['--dport', rule.ports[0]]
      elif len(rule.ports) > 1:
        args += ['-m', 'multiport', '--dport', ','.join(rule.ports)]
      else:
        self.logger.error(f'Must specify at least 1 port or None in {rule}')
        return 1

    if rule.target:
      args += ['-j', rule.target]
    
    if rule.ip_address:
      args.extend(['-s', rule.ip_address])

    # Suppress error for rule checks, since they are expected to fail
    if quiet or command == Commands.CHECK_RULE:
      stderr = subprocess.DEVNULL
    else:
      stderr = None

    try:
      cmd = " ".join(args)
      result = subprocess.call(args, stderr=stderr)
      logging.debug(f'{cmd} => {result}')
      return result
    except Exception as e:
      self.logger.error(f'Error while running {args}: {repr(e)}')
      return 1


class Commands():
  # https://linux.die.net/man/8/iptables
  APPEND_RULE = '-A'
  INSERT_RULE = '-I'
  DELETE_RULE = '-D'
  NEW_CHAIN = '-N'
  FLUSH_CHAIN = '-F'
  DELETE_CHAIN = '-X'
  CHECK_RULE = '-C'


class IPTablesBlacklist(IPTables):
  """ iptables based firewall for taserver's login server

  We add a new chain called taserver-blacklist. The chain has no default policy so will return to
  INPUT. It is assumed that the INPUT chain has a default policy of ACCEPT. When a player is banned,
  we add a rule which matches the IP -> DROP.

  We add a rule to the INPUT chain to forward traffic from client2login to taserver-blacklist chain.
  """
  
  def __init__(self, logger: Logger, ports: Ports):
    super().__init__(logger)
    self.ports = [str(ports['client2login'])]
    self.input_chain = 'INPUT'
    self.chain = f'taserver-blacklist'

  def add(self, ip_address: str) -> None:
    self.logger.info(f'{self.chain}: Adding drop rule for {ip_address}')
    rule = Rule(protocol='tcp', ports=self.ports, target='DROP', ip_address=ip_address)
    if self.iptables(Commands.CHECK_RULE, self.chain, rule) != 0:
      self.iptables(Commands.APPEND_RULE, self.chain, rule)

  def remove(self, ip_address: str) -> None:
    self.logger.info(f'{self.chain}: Removing drop rule for {ip_address}')
    self.iptables(
      Commands.DELETE_RULE,
      self.chain,
      Rule(protocol='tcp', ports=self.ports, target='DROP', ip_address=ip_address)
    )

  def remove_all(self) -> None:
    self.logger.info(f'{self.chain}: Removing all blacklist rules')
    forward_rule = Rule(protocol='tcp', ports=self.ports, target=self.chain)
    
    # Delete forwarding rule from INPUT, if it exists
    # Suppress error output since the rule may not exist
    self.iptables(Commands.DELETE_RULE, self.input_chain, forward_rule, quiet=True)

    # Delete the blacklist chain if it exists
    self.iptables(Commands.FLUSH_CHAIN, self.chain, quiet=True)
    # Delete the blacklist chain if it exists
    self.iptables(Commands.DELETE_CHAIN, self.chain, quiet=True)

  def reset(self) -> None:
    self.logger.info(f'{self.chain}: Resetting all iptables rules')
    forward_rule = Rule(protocol='tcp', ports=self.ports, target=self.chain)
    self.remove_all()

    self.logger.info(f'{self.chain}: Setting up blacklist rules')
    # Create the blacklist chain
    self.iptables(Commands.NEW_CHAIN, self.chain, quiet=True)
    
    if self.iptables(Commands.CHECK_RULE, self.input_chain, forward_rule) != 0:
      self.iptables(Commands.INSERT_RULE, self.input_chain, forward_rule)


class IPTablesWhitelist(IPTables):
  """ iptables based firewall for taserver's game_server_launcher

  We create a new chain called taserver-whitelist-$OFFSET. When a player is connected, we will add 
  a rule which matches that player's IP -> ACCEPT. The default policy for this chain is DROP

  We add rules to the INPUT chain to forward traffic for gameserver1, gameserver2, game2launcher to
  the taserver-whitelist chain.
  """

  def __init__(self, logger: Logger, ports: Ports):
    super().__init__(logger)
    self.ports = list({
      str(ports['gameserver1']),
      str(ports['gameserver2']),
      str(ports['game2launcher']),
      str(ports['launcherping'])
    })

    # The chain from which we forward traffic to the offset-specific chain
    self.input_chain = 'INPUT'
    # name of the chain for this instance of game_server_launcher
    self.chain = f'taserver-whitelist-{ports.portOffset}'

  def add(self, ip_address: str) -> None:
    self.logger.info(f'{self.chain}: Adding accept rule for {ip_address}')
    tcp_rule = Rule(protocol='tcp', ports=self.ports, target='ACCEPT', ip_address=ip_address)
    udp_rule = Rule(protocol='udp', ports=self.ports, target='ACCEPT', ip_address=ip_address)
    
    # Prepend rules to accept TCP & UDP traffic from this IP
    # Check if rules already exist to avoid duplicates
    if self.iptables(Commands.CHECK_RULE, self.chain, tcp_rule) != 0:
      self.iptables(Commands.INSERT_RULE, self.chain, tcp_rule)

    if self.iptables(Commands.CHECK_RULE, self.chain, udp_rule) != 0:
      self.iptables(Commands.INSERT_RULE, self.chain, udp_rule)

  def remove(self, ip_address: str) -> None:    
    self.logger.info(f'{self.chain}: Removing accept rule for {ip_address}')
    tcp_rule = Rule(protocol='tcp', ports=self.ports, target='ACCEPT', ip_address=ip_address)
    udp_rule = Rule(protocol='udp', ports=self.ports, target='ACCEPT', ip_address=ip_address)

    # Delete rules to accept traffic from this IP
    self.iptables(Commands.DELETE_RULE, self.chain, tcp_rule)
    self.iptables(Commands.DELETE_RULE, self.chain, udp_rule)

  def remove_all(self) -> None:
    self.logger.info(f'{self.chain}: Removing all whitelist rules')
    forward_tcp_rule = Rule(protocol='tcp', ports=self.ports, target=self.chain)
    forward_udp_rule = Rule(protocol='udp', ports=self.ports, target=self.chain)

    # Delete forwarding rules from INPUT, if it exists
    # Suppress error output since these rules may not exist
    self.iptables(Commands.DELETE_RULE, self.input_chain, forward_tcp_rule, quiet=True)
    self.iptables(Commands.DELETE_RULE, self.input_chain, forward_udp_rule, quiet=True)

    # Delete the whitelist chain, if it exists
    self.iptables(Commands.FLUSH_CHAIN, self.chain, quiet=True)
    self.iptables(Commands.DELETE_CHAIN, self.chain, quiet=True)

  def reset(self) -> None:
    self.logger.info(f'{self.chain}: Resetting all whitelist rules')
    self.remove_all()

    forward_tcp_rule = Rule(protocol='tcp', ports=self.ports, target=self.chain)
    forward_udp_rule = Rule(protocol='udp', ports=self.ports, target=self.chain)

    self.logger.info(f'{self.chain}: Setting up whitelist rules')
    # Create new taserver chain with default rule to drop all traffic
    self.iptables(Commands.NEW_CHAIN, self.chain)
    self.iptables(Commands.APPEND_RULE, self.chain, Rule(target='DROP'))
    # allow traffic from localhost so that game server and launcher can communicate
    self.iptables(Commands.INSERT_RULE, self.chain, Rule(ip_address='127.0.0.1', target='ACCEPT'))

    # Forward this game server's traffic from INPUT chain to taserver chain
    if self.iptables(Commands.CHECK_RULE, self.input_chain, forward_tcp_rule) != 0:
      self.iptables(Commands.INSERT_RULE, self.input_chain, forward_tcp_rule)
    
    if self.iptables(Commands.CHECK_RULE, self.input_chain, forward_udp_rule) != 0:
      self.iptables(Commands.INSERT_RULE, self.input_chain, forward_udp_rule)


class IPTablesFirewall():

  def __init__(self, ports: Ports, data_root: str) -> None:
    set_up_logging(data_root, 'taserver_firewall.log')
    self.logger = logging.getLogger('firewall')
    self.blacklist = IPTablesBlacklist(self.logger, ports)
    self.whitelist = IPTablesWhitelist(self.logger, ports)

  
  def remove_all_rules(self) -> None:
    self.logger.info(f'Removing all firewall rules')
    self.blacklist.remove_all()
    self.whitelist.remove_all()
  
  def run(self, server_queue: Queue) -> None:
    lists = {
      'whitelist': self.whitelist,
      'blacklist': self.blacklist
    }

    self.blacklist.reset()
    self.whitelist.reset()

    while True:
      try:
        command = server_queue.get()
        thelist = lists[command['list']]

        if command['action'] == 'reset':
            thelist.reset()
        elif command['action'] == 'add':
            ip = str(ip_address(command['ip']))
            thelist.add(ip)
        elif command['action'] == 'remove':
            ip = str(ip_address(command['ip']))
            thelist.remove(ip)
        else:
            self.logger.error('Invalid action received: %s' % command['action'])
      except Exception as e:
        self.logger.error(f'Exception while handling command: {repr(e)}')
