# -*- coding: utf-8 -*-

from PyQt4.QtCore import *
import itertools, urllib2

class OperationException(Exception):pass
class TooMuchOperationsWithSameActionException(OperationException):pass
class InvalidOperationCallbackException(OperationException):pass
class OperationAlreadyManaged(OperationException):pass
        
class Operation(object):
    
    id_counter = itertools.count(0)
    running    = {}
    done       = []
    
    def __init__(self, action, signal_done=None, signal_error=None, max_nb_tries=None, max_same=None, kill_same=False, stop_on_http_errors=True, name=None):
        """
        Create an operation, which will try to run a action. 
        - manager : the operation manager which will handle this operation
        - action : the action to be run (callback (a tuple with function and
            hash parameters), mandatory)
        - signal_done : a signal to emit if the operation is successfull.
            (a tuple with signal and list of parameters, None by default)
        - signal_error : a callback called if the operation fails (so only
            if max_nb_tries is not None). (a tuple with signal andlist of
            parameters, None by default)
        - max_nb_tries : max attempts to run the action (None or intger > 0,
            None by default)
        - max_same : max operations for the same action to run at the
            same time (None or integer > 0, None by default)
        - kill_same: kill operations with same action before trying to
            run it (Boolean, False by default)
        - stop_on_http_errors: do not try again this operation if it returns an
            http error (Boolean, True by default)
        - name: operation's name. If not defined, a name is composed with the
            action (str, None by default)
        """
        self.id      = Operation.id_counter.next()
        self.action  = self.parse_callback(action)
        self.manager = None

        try:
            self.signal_done = self.parse_signal(signal_done)
        except:
            self.signal_done = None
        try:
            self.signal_error = self.parse_signal(signal_error)
        except:
            self.signal_error = None

        self.name         = name
        self.status       = 'new'

        self.tries        = 0
        self.max_nb_tries = max_nb_tries
        self.errors       = []
        
        self.dying = False
        
        self.stop_on_http_errors = stop_on_http_errors
        
        self.make_action_str()
        running = Operation.running.setdefault(self.action_str, [])
        if running:
            if kill_same and len(running):
                for op in running:
                    try:
                        op.die()
                    except:
                        pass
            elif max_same and len(running) > max_same:
                raise TooMuchOperationsWithSameActionException
        Operation.running[self.action_str].append(self)
        
    def manage(self, manager):
        if self.manager:
            raise OperationAlreadyManaged
        self.manager = manager
        self.manager.add_operation(self)
        
    def make_action_str(self):
        callback = self.action
        try:
            if self.action[0].im_self:
                self.action_str = "%s().%s" % (self.action[0].im_class.__name__,  self.action[0].__name__)
            else:
                self.action_str = "%s.%s" % (self.action[0].im_class.__name__,  self.action[0].__name__)
        except:
            self.action_str = self.action[0].__name__
        
    def __str__(self):
        if self.max_nb_tries:
            tries_str = "%d/%d" % (self.tries, self.max_nb_tries, )
        else:
            tries_str = "%d" % self.tries
        return "Operation #%d [%s] (status=%s, tries=%s)" % (self.id, self.name or self.action_str, self.status, tries_str)
        
    def die(self):
        self.dying = True

    def parse_callback(self, callback):
        try:
            function = callback[0]
            params   = callback[1]
            if not params:
                params = {}
        except:
            function = callback
            params   = {}
        if function is None:
            raise InvalidOperationCallbackException
        return function, params
        
    def parse_signal(self, signal):
        try:
            name   = signal[0]
            params = signal[1]
            if params:
                params = [QVariant(param) for param in params]
            else:
                params = []
        except:
            name = signal
            params = []
        if not name:
            raise InvalidOperationSignalException
        return name, params

    def run_callback(self, callback):
        function,  params = callback[0], callback[1]
        return function(**params)
        
    def emit_signal(self, name, params=[]):
        self.manager.emit_signal(name, params)

    def add_error(self, exception):
        self.errors.append(exception)
        print "Error [%s] for %s" % (exception, self)

    def run(self):
        if self.status not in ('new', 'waiting'):
            return self.status
        self.status = 'running'
        self.tries += 1

        result = False
        try:
            print "Start running : %s" % self
            result = self.run_callback(self.action)
            if not result and not self.manager.gread.authenticated:
                self.die()
        except urllib2.HTTPError, e:
            self.add_error(e)
            if e.code == 401:
                if self.max_nb_tries:
                    self.max_nb_tries += 1 # do not count this try
                self.manager.set_not_authenticated()
            elif 400 <= e.code <=599:
                real_error = True
                if e.info().getheader('X-Reader-Google-Bad-Token'):
                    if self.max_nb_tries:
                        self.max_nb_tries += 1 # do not count this try
                    real_error = False
                    self.manager.set_not_authenticated()
                if real_error and self.stop_on_http_errors:
                    self.display_message("Operation [%s] canceled : %s" % (self.name or self.action_str, e))
                    self.die()
        except urllib2.URLError, e:
            if self.max_nb_tries:
                self.max_nb_tries += 1 # do not count this try
            self.add_error(e)
            self.manager.set_no_network()
        except Exception, e:
            self.add_error(e)

        if result:
            self.status = 'done'
            try:
                Operation.running[self.action_str].remove(self)
            except:
                pass
            Operation.done.append(self)
            if self.signal_done:
                try:
                    self.emit_signal(self.signal_done[0], self.signal_done[1])
                except Exception, e:
                    self.add_error(OperationException("Error in signal_done %s : %s" % (self.signal_done[0], e)))
        elif self.dying or (self.max_nb_tries is not None and self.tries >= self.max_nb_tries):
            if self.dying:
                self.status = 'killed'
            else:
                self.status = 'error'
            if self.signal_error:
                try:
                    self.emit_signal(self.signal_error[0], self.signal_error[1])
                except Exception, e:
                    self.add_error(OperationException("Error in signal_error %s : %s" % (self.signal_error[0], e)))
        elif self.status == 'running':
            self.status = 'waiting'
            
        print "End running : %s" % self
        return self.status
        
class OperationManager(QThread):

    def __init__(self, gread, test_auth_url, parent=None):
        super(OperationManager, self).__init__(parent)
        self.gread = gread
        self.operations = []
        self.current_operation = None
        self.test_auth_request = urllib2.Request(test_auth_url)
        self.no_network = False

    def add_operation(self, operation):
        self.operations.insert(0, operation)
        self.emit_signal("operation_added")
        if self.no_network:
            self.alert_no_network()
        elif not self.gread.authenticated:
            if self.gread.previously_authenticated:
                self.alert_not_authenticated()
        if not self.isRunning():
            self.start()

    def set_no_network(self, alert=True):
        self.no_network = True
        if alert:
            self.alert_no_network()
        while True:
            try:
                response = urllib2.urlopen(self.test_auth_request)
            except urllib2.HTTPError:
                self.no_network = False
            except urllib2.URLError, e:
                self.sleep(10)
            else:
                response.close()
                self.no_network = False
            if not self.no_network:
                break
        
    def emit_signal(self, name, params=[]):
        self.emit(SIGNAL(name), *params)
                
    def display_message(self, message, level="information"):
        self.emit_signal("display_message", [message, level, ])
        
    def get_nb_operations(self):
        nb = len(self.operations)
        if self.current_operation:
            nb += 1
        return nb
                
    def alert_no_network(self):
        todo = []
        nb = self.get_nb_operations()
        if nb:
            todo.append("running %d operations" % nb)
        if not self.gread.authenticated:
            todo.append("authenticating")
        self.display_message("Network connection lost. Waiting %s" % (" and ".join(todo) or "!"), 'critical')
        
    def alert_not_authenticated(self):
        nb = self.get_nb_operations()
        self.display_message("Bad Google Reader session. Authenticating... (%d operations remaining" % nb, 'critical')

    def set_not_authenticated(self, alert=True):
        if alert:
            self.alert_not_authenticated()
        while True:
            try:
                self.gread.authenticate()
                if self.gread.authenticated or not self.gread.previously_authenticated:
                    break
                self.sleep(10)
            except urllib2.URLError:
                self.set_no_network()
            except:
                if not self.gread.previously_authenticated:
                    break
                self.sleep(10)

    def run(self):
        while self.operations:
            try:
                self.current_operation = self.operations.pop()
            except:
                pass
            else:
                self.emit_signal("operation_start_running")
                result = self.current_operation.run()
                if result == 'waiting':
                    self.add_operation(self.current_operation)
                self.current_operation = None
                self.emit_signal("operation_stop_running")
