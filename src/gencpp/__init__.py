# Software License Agreement (BSD License)
#
# Copyright (c) 2011, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above
# copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided
# with the distribution.
# * Neither the name of Willow Garage, Inc. nor the names of its
# contributors may be used to endorse or promote products derived
# from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import genmsg.msgs
import genmsg.msg_loader

try:
    from cStringIO import StringIO #Python 2.x
except ImportError:
    from io import StringIO #Python 3.x

MSG_TYPE_TO_CPP = {'byte': 'int8_t',
                   'char': 'uint8_t',
                   'bool': 'uint8_t',
                   'uint8': 'uint8_t',
                   'int8': 'int8_t',
                   'uint16': 'uint16_t',
                   'int16': 'int16_t',
                   'uint32': 'uint32_t',
                   'int32': 'int32_t',
                   'uint64': 'uint64_t',
                    'int64': 'int64_t',
                   'float32': 'float',
                   'float64': 'double',
                   'string': 'std::basic_string<char, std::char_traits<char>, typename ContainerAllocator::template rebind<char>::other > ',
                   'time': 'ros::Time',
                   'duration': 'ros::Duration'}

#used
def msg_type_to_cpp(type):
    """
    Converts a message type (e.g. uint32, std_msgs/String, etc.) into the C++ declaration
    for that type (e.g. uint32_t, std_msgs::String_<ContainerAllocator>)

    @param type: The message type
    @type type: str
    @return: The C++ declaration
    @rtype: str
    """
    (base_type, is_array, array_len) = genmsg.msgs.parse_type(type)
    cpp_type = None
    if (genmsg.msgs.is_builtin(base_type)):
        cpp_type = MSG_TYPE_TO_CPP[base_type]
    elif (len(base_type.split('/')) == 1):
        if (genmsg.msgs.is_header_type(base_type)):
#            cpp_type = ' ::std_msgs::Header_<ContainerAllocator> '
            cpp_type = ' ::std_msgs::Header '
        else:
#            cpp_type = '%s_<ContainerAllocator> '%(base_type)
            cpp_type = '%s '%(base_type)
    else:
        pkg = base_type.split('/')[0]
        msg = base_type.split('/')[1]
#        cpp_type = ' ::%s::%s_<ContainerAllocator> '%(pkg, msg)
        cpp_type = ' ::%s::%s '%(pkg, msg)

    if (is_array):
        if (array_len is None):
            raise
#            return 'std::vector<%s, typename ContainerAllocator::template rebind<%s>::other > '%(cpp_type, cpp_type)
#            return 'std::vector<%s, typename ContainerAllocator::template rebind<%s>::other > '%(cpp_type, cpp_type)
        else:
            return 'boost::array<%s, %s> '%(cpp_type, array_len)
    else:
        return cpp_type

def _escape_string(s):
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    return s

def escape_message_definition(definition):
    lines = definition.splitlines()
    if not lines:
        lines.append('')
    s = StringIO()
    for line in lines:
        line = _escape_string(line)
        s.write('%s\\n\\\n'%(line))
        
    val = s.getvalue()
    s.close()
    return val

#used2
def cpp_message_declarations(name_prefix, msg):
    """
    Returns the different possible C++ declarations for a message given the message itself.

    @param name_prefix: The C++ prefix to be prepended to the name, e.g. "std_msgs::"
    @type name_prefix: str
    @param msg: The message type
    @type msg: str
    @return: A tuple of 3 different names.  cpp_message_decelarations("std_msgs::", "String") returns the tuple
        ("std_msgs::String_", "std_msgs::String_<ContainerAllocator>", "std_msgs::String")
    @rtype: str
    """
    pkg, basetype = genmsg.names.package_resource_name(msg)
    cpp_name = ' ::%s%s'%(name_prefix, msg)
    if (pkg):
        cpp_name = ' ::%s::%s'%(pkg, basetype)
    return ('%s_'%(cpp_name), '%s_<ContainerAllocator> '%(cpp_name), '%s'%(cpp_name))

#todo
def is_fixed_length(spec, msg_context, includepath):
    """
    Returns whether or not the message is fixed-length

    @param spec: The message spec
    @type spec: genmsg.msgs.MsgSpec
    @param package: The package of the
    @type package: str
    """
    types = []
    for field in spec.parsed_fields():
        if (field.is_array and field.array_len is None):
            return False

        if (field.base_type == 'string'):
            return False

        if (not field.is_builtin):
            types.append(field.base_type)

    types = set(types)
    for t in types:
        t = genmsg.msgs.resolve_type(t, spec.package)
        assert isinstance(includepath, dict)
        new_spec = genmsg.msg_loader.load_msg_by_type(msg_context, t, includepath)
        if (not is_fixed_length(new_spec, msg_context, includepath)):
            return False

    return True

#used2
def default_value(type):
    """
    Returns the value to initialize a message member with.  0 for integer types, 0.0 for floating point, false for bool,
    empty string for everything else

    @param type: The type
    @type type: str
    """
    if type in ['byte', 'int8', 'int16', 'int32', 'int64',
                'char', 'uint8', 'uint16', 'uint32', 'uint64']:
        return '0'
    elif type in ['float32', 'float64']:
        return '0.0'
    elif type == 'bool':
        return 'false'

    return ""
#used2
def takes_allocator(type):
    """
    Returns whether or not a type can take an allocator in its constructor.  False for all builtin types except string.
    True for all others.

    @param type: The type
    @type: str
    """
    return not type in ['byte', 'int8', 'int16', 'int32', 'int64',
                        'char', 'uint8', 'uint16', 'uint32', 'uint64',
                        'float32', 'float64', 'bool', 'time', 'duration']

def escape_string(str):
    str = str.replace('\\', '\\\\')
    str = str.replace('"', '\\"')
    return str

#used
def generate_fixed_length_assigns(spec, container_gets_allocator, cpp_name_prefix):
    """
    Initialize any fixed-length arrays

    @param s: The stream to write to
    @type s: stream
    @param spec: The message spec
    @type spec: genmsg.msgs.MsgSpec
    @param container_gets_allocator: Whether or not a container type (whether it's another message, a vector, array or string)
        should have the allocator passed to its constructor.  Assumes the allocator is named _alloc.
    @type container_gets_allocator: bool
    @param cpp_name_prefix: The C++ prefix to use when referring to the message, e.g. "std_msgs::"
    @type cpp_name_prefix: str
    """
    # Assign all fixed-length arrays their default values
    for field in spec.parsed_fields():
        if (not field.is_array or field.array_len is None):
            continue

        val = default_value(field.base_type)
        if (container_gets_allocator and takes_allocator(field.base_type)):
            # String is a special case, as it is the only builtin type that takes an allocator
            if (field.base_type == "string"):
                string_cpp = msg_type_to_cpp("string")
                yield '    %s.assign(%s(_alloc));\n'%(field.name, string_cpp)
            else:
                (cpp_msg_unqualified, cpp_msg_with_alloc, _) = cpp_message_declarations(cpp_name_prefix, field.base_type)
                yield '    %s.assign(%s(_alloc));\n'%(field.name, cpp_msg_with_alloc)
        elif (len(val) > 0):
            yield '    %s.assign(%s);\n'%(field.name, val)

#used
def generate_initializer_list(spec, container_gets_allocator):
    """
    Writes the initializer list for a constructor

    @param s: The stream to write to
    @type s: stream
    @param spec: The message spec
    @type spec: genmsg.msgs.MsgSpec
    @param container_gets_allocator: Whether or not a container type (whether it's another message, a vector, array or string)
        should have the allocator passed to its constructor.  Assumes the allocator is named _alloc.
    @type container_gets_allocator: bool
    """

    op = ':'
    for field in spec.parsed_fields():
        val = default_value(field.base_type)
        use_alloc = takes_allocator(field.base_type)
        if (field.is_array):
            if (field.array_len is None and container_gets_allocator):
                yield '  %s %s(_alloc)'%(op, field.name)
            else:
                yield '  %s %s()'%(op, field.name)
        else:
            if (container_gets_allocator and use_alloc):
                yield '  %s %s(_alloc)'%(op, field.name)
            else:
                yield '  %s %s(%s)'%(op, field.name, val)
        op = ','


#
# code added for subsystem_buffers
#

def parse_comment_to_subsystem_buffer_spec(comment):
    id_str = 'subsystem_buffer{'

    pos_beg = comment.find(id_str)
    if pos_beg < 0:
        return None

    pos_end = comment.find('}', pos_beg)
    if pos_end < 0:
        # subsystem_buffer declaration must be complete
        return None

    decl = comment[pos_beg + len(id_str) : pos_end]
    decl_list = decl.split(';')

    decl_dict = {}
    for item in decl_list:
        pos = item.find(':')
        if pos < 0:
            continue
        decl_dict[item[:pos].strip()] = item[pos+1:].strip()

    if not 'type' in decl_dict:
        return None
    type = decl_dict['type']

    validity_field_name = ''
    if 'validity' in decl_dict:
        validity_field_name = decl_dict['validity']

#    if type == 'container' and len(decl_list) == 2:
#        validity_field_name = decl_list[1].strip()
#        return (port_type, validity_field_name)
    data_type = ''
    if type == 'port':
        if not 'data_type' in decl_dict:
            return None
        data_type = decl_dict['data_type']

    includes = []
    if 'includes' in decl_dict:
        for inc in decl_dict['includes'].split(','):
            includes.append(inc.strip())

#        internal_type_name = decl_list[1].strip()
#        validity_field_name = decl_list[2].strip()
#        return (port_type, internal_type_name, validity_field_name)

    return (type, validity_field_name, data_type, includes)

def get_port_spec_dict(spec):
    port_spec_dict = {}
    # process msg declaration line by line, search for port_spec
    for line in spec.text.splitlines():
        comment_start = line.find('#')
        if comment_start <= 0:
            continue
        declaration = line[:comment_start-1]
        comment = line[comment_start:]
        success = True
        try:
            field_type, name = genmsg.msg_loader._load_field_line(declaration, spec.package)
        except:
            success = False
        if success:
            port_spec = parse_comment_to_subsystem_buffer_spec(comment)
            if port_spec != None:
                port_spec_dict[name] = port_spec

    return port_spec_dict

def generate_additional_includes(spec):
    port_spec_dict = get_port_spec_dict(spec)
    includes = []
    for name in port_spec_dict:
        includes = includes + port_spec_dict[name][3]
    for inc in includes:
        yield '#include %s'%(inc)

def generate_member_list_input(spec):
    port_spec_dict = get_port_spec_dict(spec)

    for field in spec.parsed_fields():
        if field.name in port_spec_dict:
            port_spec = port_spec_dict[field.name]
            if port_spec[0] == 'container':
                if field.is_builtin:
                    raise
                yield '  %s_InputPorts %s_;'%(msg_type_to_cpp(field.type)[:-1], field.name)
            elif port_spec[0] == 'port':
                yield '  RTT::InputPort<Container_::_%s_type > %s_;'%(field.name, field.name)

def generate_member_list_output(spec):
    port_spec_dict = get_port_spec_dict(spec)

    for field in spec.parsed_fields():
        if field.name in port_spec_dict:
            port_spec = port_spec_dict[field.name]
            if port_spec[0] == 'container':
                if field.is_builtin:
                    raise
                yield '  %s_OutputPorts %s_;'%(msg_type_to_cpp(field.type)[:-1], field.name)
            elif port_spec[0] == 'port':
                yield '  RTT::OutputPort<Container_::_%s_type > %s_;'%(field.name, field.name)

def generate_ports_initializer_list(spec):
    port_spec_dict = get_port_spec_dict(spec)
    op = ':'
    for field in spec.parsed_fields():
        if field.name in port_spec_dict:
            port_spec = port_spec_dict[field.name]
            if port_spec[0] == 'container':
                yield '    %s %s_(tc, prefix + std::string(prefix.empty()?"":"_") + \"%s\")'%(op, field.name, field.name)
                op = ','
            else:
                yield '    %s %s_(prefix + std::string(prefix.empty()?"":"_") + \"%s\")'%(op, field.name, field.name)
                op = ','

def generate_ports_constructor_code(spec):
    port_spec_dict = get_port_spec_dict(spec)
    op = ','
    for field in spec.parsed_fields():
        if field.name in port_spec_dict:
            port_spec = port_spec_dict[field.name]
            if port_spec[0] == 'port':
                yield 'tc.addPort(%s_);'%(field.name)

def generate_read_ports_list(spec):
    port_spec_dict = get_port_spec_dict(spec)
    for field in spec.parsed_fields():
        if field.name in port_spec_dict:
            port_spec = port_spec_dict[field.name]
            validity_field = port_spec[1]
            if validity_field:
                yield 'ros.%s = %s_.read(ros.%s);'%(validity_field, field.name, field.name)
            else:
                yield 'result &= %s_.read(ros.%s);'%(field.name, field.name)

# TODO: default value
#            yield '  if (!%s_valid_) {'%(field.name)
#            val = default_value(field.base_type)
#            if field.is_array:
#                yield '    ros.%s = %s();'%(field.name, msg_type_to_cpp(field.type))
#            else:
#                yield '    ros.%s = %s(%s);'%(field.name, msg_type_to_cpp(field.type), val)
#            yield '  }'

def generate_write_ports_list(spec):
    port_spec_dict = get_port_spec_dict(spec)
    for field in spec.parsed_fields():
        if field.name in port_spec_dict:
            port_spec = port_spec_dict[field.name]
            validity_field = port_spec[1]
            if validity_field:
                yield 'if (ros.%s) {'%(validity_field)
                yield '    %s_.write(ros.%s);'%(field.name, field.name)
                yield '}'
            else:
                yield '%s_.write(ros.%s);'%(field.name, field.name)

def generate_convert_from_ros_list(spec):
    port_spec_dict = get_port_spec_dict(spec)
    for field in spec.parsed_fields():
        if field.name in port_spec_dict:
            port_spec = port_spec_dict[field.name]
            yield '  %s_.convertFromROS(ros.%s);'%(field.name, field.name)
            validity_field = port_spec[1]
            if validity_field:
                yield '  %s_valid_ = ros.%s;'%(field.name, validity_field)

def generate_convert_to_ros_list(spec):
    op = 'if ('
    close_block = False
    port_spec_dict = get_port_spec_dict(spec)
    for field in spec.parsed_fields():
        if field.name in port_spec_dict:
            port_spec = port_spec_dict[field.name]
            validity_field = port_spec[1]
            if not validity_field:
                yield '  %s !%s_valid_'%(op, field.name)
                op = '||'
                close_block = True;

    if close_block:
        yield ') {'
        yield '  ros = Container_();'
        yield '}'
        yield 'else {'

    for field in spec.parsed_fields():
        if field.name in port_spec_dict:
            port_spec = port_spec_dict[field.name]
            yield '  if (%s_valid_) {'%(field.name)
            yield '    %s_.convertToROS(ros.%s);'%(field.name, field.name)
            yield '  }'
            yield '  else {'
            val = default_value(field.base_type)
            if field.is_array:
                yield '    ros.%s = %s();'%(field.name, msg_type_to_cpp(field.type))
            else:
                yield '    ros.%s = %s(%s);'%(field.name, msg_type_to_cpp(field.type), val)
            yield '  }'
            validity_field = port_spec[1]
            if validity_field:
                yield '  ros.%s = %s_valid_;'%(validity_field, field.name)

    if close_block:
        yield '}'

