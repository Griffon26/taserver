#!/usr/bin/env python3
#
# Copyright (C) 2018  Maurice van der Pot <griffon26@kfk4ever.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# TODO:
# Get rid of duplication between normal tracer and dict tracer

from datetime import datetime


def _make_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]


class RefOnly:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class StateTracer:
    def __init__(self, obj, members_to_trace):
        #print('Creating %s with obj %s' % (self, obj))
        self.prefix = ''
        self.obj = obj
        self.enabled = False
        self.members_to_trace = [str(name) for name in members_to_trace]
        self.refonly_members = set(str(name) for name in members_to_trace if isinstance(name, RefOnly))

    def add_to_trace(self, member_name):
        #print('add_to_trace: %s' % member_name)
        assert hasattr(self.obj, member_name)
        self.members_to_trace.add(member_name)
        if self.enabled:
            self.member_changed(member_name, None, getattr(self.obj, member_name))

    def _trace(self, member_name, value):
        print('%s - STATETRACE - %s.%s = %s' % (_make_timestamp(), self.prefix, member_name,
                                                repr(value) if isinstance(value, str) else value))

    def member_changed(self, member_name, old_value, new_value):
        #print('member_changed: %s from %s to %s (trace is %s, members to trace: %s)' % (member_name, old_value, new_value, self.enabled, self.members_to_trace))
        assert member_name in self.members_to_trace
        if self.enabled:
            if member_name not in self.refonly_members:
                if hasattr(old_value, '_state_tracer'):
                    old_value._state_tracer._stop()

                if hasattr(new_value, '_state_tracer'):
                    #print('calling _start on new_value %s\'s state_tracer %s' % (new_value, new_value._state_tracer))
                    #print('Starting trace and passing "%s.%s"' % (self.prefix, member_name))
                    new_value._state_tracer._start('%s.%s' % (self.prefix, member_name))
                else:
                    self._trace(member_name, new_value)
            else:
                self._trace(member_name, new_value)

    def _start(self, prefix):
        #print('%s: _start' % self)
        assert not self.enabled
        self.enabled = True
        self.prefix = prefix

        for member_name in self.members_to_trace:
            member_to_start = getattr(self.obj, member_name)
            #print('calling _start on %s\'s member %s\'s tracer %s' % (self.obj, member_to_start, member_to_start._state_tracer))
            if hasattr(member_to_start, '_state_tracer') and member_name not in self.refonly_members:
                #print('Starting trace2 and passing "%s:%s"' % (prefix, member_name))
                member_to_start._state_tracer._start('%s.%s' % (prefix, member_name))
            else:
                self._trace(member_name, member_to_start)


    def _stop(self):
        assert self.enabled
        self.enabled = False
        self.prefix = None

        for member_name in self.members_to_trace:
            member_to_stop = getattr(self.obj, member_name)
            if hasattr(member_to_stop, '_state_tracer') and member_name not in self.refonly_members:
                member_to_stop._state_tracer._stop()


class DictStateTracer:
    def __init__(self, obj, refsonly):
        #print('Creating %s with obj %s' % (self, obj))
        self.prefix = ''
        self.obj = obj
        self.enabled = False
        self.refsonly = refsonly

    def _trace(self, member_name, value):
        print('%s - STATETRACE - %s[%s] = %s' % (_make_timestamp(), self.prefix, member_name,
                                                 repr(value) if isinstance(value, str) else value))

    def _trace_event(self, member_name, event):
        print('%s - STATETRACE - %s[%s] %s' % (_make_timestamp(), self.prefix, member_name, event))

    def member_changed(self, member_name, old_value, new_value):
        #print('member_changed: %s from %s to %s' % (member_name, old_value, new_value))
        if self.enabled:
            if not self.refsonly:
                if hasattr(old_value, '_state_tracer'):
                    old_value._state_tracer._stop()

                if hasattr(new_value, '_state_tracer'):
                    #print('calling _start on new_value %s\'s state_tracer %s' % (new_value, new_value._state_tracer))
                    new_value._state_tracer._start('%s[%s]' % (self.prefix, member_name))
                else:
                    self._trace(member_name, new_value)
            else:
                self._trace(member_name, new_value)

    def member_added(self, member_name, new_value):
        if self.enabled:
            self._trace_event(member_name, 'added')
            self.member_changed(member_name, None, new_value)

    def member_removed(self, member_name, old_value):
        #print('member_changed: %s from %s to %s' % (member_name, old_value, new_value))
        if self.enabled:
            if hasattr(old_value, '_state_tracer') and not self.refsonly:
                old_value._state_tracer._stop()

            self._trace_event(member_name, 'removed')

    def _start(self, prefix):
        #print('%s: _start' % self)
        assert not self.enabled
        self.enabled = True
        self.prefix = prefix

        for member_name, member_to_start in self.obj.items():
            #print('calling _start on %s\'s member %s\'s tracer %s' % (self.obj, member_to_start, member_to_start._state_tracer))
            if hasattr(member_to_start, '_state_tracer') and not self.refsonly:
                member_to_start._state_tracer._start('%s.%s' % (prefix, member_to_start))
            else:
                self._trace(member_name, member_to_start)


    def _stop(self):
        assert self.enabled
        self.enabled = False
        self.prefix = None

        for member_name, member_to_stop in self.obj.items():
            if hasattr(member_to_stop, '_state_tracer') and not self.refsonly:
                member_to_stop._state_tracer._stop()

class TracingDict(dict):

    def __init__(self, *args, **kwargs):
        if 'refsonly' in kwargs:
            refsonly = kwargs['refsonly']
            del kwargs['refsonly']
        else:
            refsonly = False
        self._state_tracer = DictStateTracer(self, refsonly)
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, new_value):
        if key in self:
            old_value = self[key]
            self._state_tracer.member_changed(key, old_value, new_value)
        else:
            self._state_tracer.member_added(key, new_value)
        return super().__setitem__(key, new_value)

    def __delitem__(self, key):
        self._state_tracer.member_removed(key, self[key])
        return super().__delitem__(key)

    def pop(self, key, *args):
        if key in self:
            self._state_tracer.member_removed(key, self[key])
        return super().pop(key, *args)

def setup_properties(cls, members):

        for name in members:
            def create_property(name):
                #print('creating property %s' % name)
                actual_member_name = '_' + name

                def getter(self):
                    #print('running generated getter for %s' % name)
                    return getattr(self, actual_member_name)

                def setter(self, new_value):
                    #print('running generated setter for %s with value %s' % (name, new_value))
                    old_value = getattr(self, actual_member_name) if hasattr(self, actual_member_name) else None
                    setattr(self, actual_member_name, new_value)
                    getattr(self, '_state_tracer').member_changed(name, old_value, new_value)

                prop = property(getter, setter)
                return prop

            setattr(cls, name, create_property(name))

def statetracer(*member_name_list):
    def real_decorator(cls):
        setup_properties(cls, [str(name) for name in member_name_list])

        cls._original_init = getattr(cls, '__init__', lambda self : None)

        def new_init(self, *args, **kwargs):
            self._state_tracer = StateTracer(self, member_name_list)
            self._original_init(*args, **kwargs)
            for member_name in member_name_list:
                assert hasattr(self, '_%s' % member_name), \
                       'Member \'%s\' mentioned in the statetracer decorator ' \
                       'was not created in the __init__ of class %s' % (member_name, type(self).__name__)

        cls.__init__ = new_init

        def trace_as(self, name):
            self._state_tracer._start(name)

        cls.trace_as = trace_as

        return cls

    return real_decorator


@statetracer('member1', 'member2')
class ExampleClass:

    def __init__(self):
        self.member1 = None
        self.member2 = None

    def __str__(self):
        return 'ExampleClass(member1 = %s, member2 = %s)' % (self.member1, self.member2)


if __name__ == '__main__':
    print('Creating example class instance...')
    obj = ExampleClass()

    print('Enabling tracing on this instance as "root"')
    obj.trace_as('root')

    print('Creating another example class instance...')
    subobj = ExampleClass()

    print('Assigning "membervalue1" to member1 of second instance...')
    subobj.member1 = 'membervalue1'
    print('Assigning "{1: 2, 5: 6}" to member2 of second instance...')
    subobj.member2 = TracingDict({1: 2, 5: 6})

    print('Assigning second instance to member1 of first instance...')
    obj.member1 = subobj

    print('Adding key 3 with value 4 to member2 of second instance...')
    obj.member1.member2[3] = 4


