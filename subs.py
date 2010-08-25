
# Imports
import re

# Use these methods directly, without the 're' prefix
from re import sub, match



## Functions used in the main loop

# Pull the template from the page text
def GetExtensionTemplate(page_text):
    # Normally it wouldn't be this simple, but the extension templates
    # are usually well formatted, each ending with \n}}.

    # We could recursively look for sub templates to be more sure
    # we're at the end.
    
    template_start = re.search('^{{Extension', page_text, re.I | re.M)

    if template_start:
        end_pattern = re.compile('^}}', re.M)
        template_end = end_pattern.search(page_text, template_start.end())

        if template_end:
            return page_text[template_start.start():template_end.end()]
        else:
            print 'no end!'
    else:
        print 'no start!'
    return 0



# converts an extension dict back into template format
def BuildExtensionTemplate(extension_dict):
    template = '{{ExtensionMatrix\n'
    keys = extension_dict.keys()
    for key in keys:
        # This guy giving me a hard time for some reason
        if '<!-' in extension_dict[key] or '-->' in extension_dict[key]:
            print 'foo!'
            continue
        # Build this line of the template
        template += '|' + key + '=' + extension_dict[key] + '\n'

    template += '}}\n'
    return template



def DateFormat(mwdate):
    ## Get the date in 'ISO' format for SMW
    ## http://semantic-mediawiki.org/wiki/Type:Date
    return '%04d-%02d-%02dT%02d:%02d:%02d' % (mwdate.tm_year, mwdate.tm_mon, mwdate.tm_mday, mwdate.tm_hour, mwdate.tm_min, mwdate.tm_sec)










## Functions used by the ParseExtensionTemplate Function

# versh
def GetVersh(version_text):
    # Figure out what versions of mediawiki this extension works on
    # this just looks for a string match of the version. I personally
    # don't trust the +,>=,etc... sign people like to use, for
    # example, 1.12+.  That generally means that they tested it on
    # 1.12, but not the versions that came afterwards. Really sketchy
    # is >=1.6. Yeah right!

    supported_versions = []

    # TODO: this will break if mw goes past 1.20 or into 2.x
    for version in xrange(2,20): 
        this_version = '1.' + str(version)
        if version_text.find(this_version) != -1:
            supported_versions.append(this_version)

    return ', '.join(supported_versions)



# The ParseExtensionTemplate Function

# Parse and cleanup template text
def ParseExtensionTemplate(template_text):

    # With just a little work we can turn the template into a
    # dictionary and then do some cleanup processing of its
    # parameters. This bot is definitely relying on the fact that the
    # template ends with \n}}

    # If there is a newline in a template parameter, that's probably
    # going to mess things up!!!

    extension_dict = {}
    hooks, tags, types = [], [], []



    # Some people like to have funky spacing
    template_text = sub(' *\| *', '|', template_text)



    # This hacks off '{{Extension' and '}}', and has the convenient
    # side effect of nuking '|templatemode=' when it shows up on the
    # first line
    template_param = template_text.split('\n')[1:-1]



    # Can't allow newlines - saw way too many crazy template
    # values. In order for this to be sane, the template must have a
    # pipe as the first non whitespace char on each line

    filtered_template_param = []

    for param in template_param:
        if match('^\s*\|', param):
            filtered_template_param.append(param)
        else:
            print('failed to match template parameter! : ' + param)

    template_param = filtered_template_param



    # Process each parameter
    # Check and clean-up parameter values

    for param in template_param:
        try:
            param = param.split('=', 1)
            key = param[0].replace('|', '').strip()
            value = param[1].strip()
        except:
            # Can't do this? Not my fault! Next param!
            continue

        # Skip parameters with empty values
        if not len(value):
            continue

        # Remove HTML comments from the value
        value = sub('<!--.*?-->', '', value)

        # Remove ref tags from the value
        if '<ref>' in value:
            value = value.replace('<ref>', ' ')
        if '</ref>' in value:
            value = value.replace('</ref>', ' ')

        # Have a look at LocalisationUpdate for nested templateness
        # that is just not ok.
        if '{{' in value and not '}}' in value:
            continue
        if '}}' in value and not '{{' in value:
            continue

        # Process the values of certain parameters in certain ways
        if key.find('hook') is not -1:
            hooks.append(value)
            continue
        if key.find('tag') is not -1:
            tags.append(value)
            continue
        if key.find('type') is not -1:
            types.append(value.lower())
            continue

        if key.find('author') is not -1:
            # clean up!
            value = value
        
#        if key.find('download') is not -1:
#            # Fix a special case
#            if value.match(
#            # Remove wiki text
#            value = sub('^\[', '', value)
#            value = sub('\]$', '', value)

        if key.find('example') is not -1:
            # Remove wiki text
            value = sub('^\[', '', value)
            value = sub('\]$', '', value)
        
        if key.find('status') is not -1:
            # Make sure this is a single word status - sanity check
            if len(value.split(' ')) == 1:
                value = value.lower()

        if key.find('mediawiki') is not -1:
            # sort the thing
            value = GetVersh(value)



        # Store them!
        extension_dict[key] = value

    if hooks:
        hooks.sort()
        hooks = ', '.join(hooks)
        extension_dict['hooks'] = hooks
    if tags:
        tags.sort()
        tags = ', '.join(tags)
        extension_dict['tags'] = tags   
    if types:
        types.sort()
        types = ', '.join(types)
        extension_dict['types'] = types



    # Don't allow empty templates, or templates with just one
    # parameter
    
    keys = extension_dict.keys()
    if not len(keys) or len(keys) == 1:
        print('discarding extension (empty)')
        raise

    return( extension_dict )

