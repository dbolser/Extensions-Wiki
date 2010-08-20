# Username and password for the MW site
mw_username = '' # anon is fine
mw_password = '' # 

# Username and password for the SMW site
smw_username = 'DMBot'
smw_password = 'botty'



# Imports
from re import sub, match
from sys import path
from dateutil.parser import parse
import datetime
path.append('./mwclient')
path.append('./mwclient/simplejson')
import client as mwclient



# Get a 'site' object and login
mw_site = mwclient.Site('www.mediawiki.org', path='/w/')
mw_site.login(mw_username, mw_password)

# Get a 'site' object and login
smw_site = mwclient.Site('extensions.referata.com', path='/w/')
smw_site.login(smw_username, smw_password)

# Get a list of all the pages in the 'all extensions' category
all_extensions = mw_site.categories["All extensions"]



# What are these? Seem to match sections here:
# http://www.mediawiki.org/wiki/User:Alterego/ExtensionMatrix
extensions, extension_dicts = {}, {}



# converts an extension dict back into template format
def BuildExtensionTemplate(extension_dict):
    template = '{{ExtensionMatrix\n'
    keys = extension_dict.keys()
    for key in keys:
        # This guy giving me a hard time for some reason
        if '<!-' in extension_dict[key] or '-->' in extension_dict[key]:
            continue
        # Build this line of the template
        template += '|' + key + '=' + extension_dict[key] + '\n'

    template += '}}\n'
    return template



# 
def GetExtensionTemplate(extension_text):
    # Normally wouldn't be this simple but the extensions are well
    # formatted, each ending with \n}}. Could recursively look for sub
    # templates to be more sure we're at the end.

    template_start = extension_text.find('{{Extension')

    if template_start == -1:
        template_start = extension_text.find('{{extension')

    if template_start == -1:
        return 0

    template_end = extension_text[template_start:].find('\n}}')

    if template_end == -1:
        return 0

    template_end = template_start + template_end

    return wikitext[template_start:template_end+3]



###############################################
# Download the template_text for each extension
###############################################

for this_extension in all_extensions:
    try:
        extension_name = this_extension.name.split(':')[1]

        ## Debugging
        print extension_name

        # Don't allow subpage extensions
        if '/' in extension_name:
            print 'discarding (subpage) : ' + extension
            continue

        # Keep empty vals around to create a list of poorly formatted
        # extensions
        extensions[extension_name] = ''

        # Extract the wikitext.
        try:
            wikitext = this_extension.edit()
        except:
            exit('couldnt get page text!')

        template_text = GetExtensionTemplate(wikitext)

        if template_text == 0:
            exit()

        extensions[extension_name] = template_text
        
        ## Debugging
        #if(len(extensions) > 3):
        #    break

    except:
        # If someone did something stupid, not worth breaking the bot
        print('failed to find extension template! : ' + extension_name)
        continue
#exit()


print 'got %d extensions' % len(extensions)



# With just a little work we can turn the template into a dictionary
# and then do some cleanup processing of its parameters. This bot is
# definitely relying on the fact that the template ends with \n}}

for extension in extensions.keys():

    extension_dict = {}
    hooks, tags, types = [], [], []

    template_text = extensions[extension]

    # If there is a newline in a template parameter, that's probably
    # going to mess things up

    # Some people like to have funky spacing. Double up just in case
    template_text = sub(' *\| *', '|', template_text)

    # This hacks off '{{Extension' and '}}', and has the convenient
    # side effect of nuking '|templatemode=' when it shows up on the
    # first line
    template_param = template_text.split('\n')[1:-1]

    # Can't allow newlines - saw way too many crazy template
    # values. In order for this to be sane, the template must have a
    # pipe as the first non whitespace char on each line
    filtered_template_param = []
    for line in template_param:
        if match('^\s*\|', line):
            filtered_template_param.append(line)
        else:
            print('failed to match!')

    template_param = filtered_template_param

    for param in template_param:
        try:
            param = param.split('=', 1)
            key = param[0].replace('|', '').strip()
            value = param[1].strip()
        except:
            continue # Can't do this? Not my fault.



        # Check and clean-up values
        if not len(value):
            continue

        # Remove HTML comments from value
        value = sub('<!--.*?-->', '', value)

        # Remove ref tags from value
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



        # Process certain tags in certain ways
        if 'name' in key:
            # Sometimes the name field doesn't contain the actual name
            # of the extension
            value = extension
        if key.find('hook') is not -1:
            hooks.append(value)
            continue
        if key.find('tag') is not -1:
            tags.append(value)
            continue
        if key.find('type') is not -1:
            types.append(value.lower())
            continue
        
        if key.find('status') is not -1:
            # Make sure this is a single word status - sanity check
            if len(value.split(' ')) == 1:
                value = value.lower()

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

    # Sometimes the name isn't specified at all
    if not extension_dict.has_key('name'):
        extension_dict['name'] = extension

    # Don't allow empty templates, or templates with just one
    # parameter
    keys = extension_dict.keys()
    if not len(keys) or len(keys) == 1:
        print('discarding (empty) : ' + extension)
        continue

    extension_dicts[extension] = extension_dict
#exit()


print 'got %d extensions' % len(extension_dicts)





# convert all parseable dates into a common wikitable-sortable format
# months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
# for extension in extension_dicts.keys():
#     if extension_dicts[extension].has_key('update'):
#         try:
#             this_date = parse(extension_dicts[extension]['update'])
#             this_day = this_date.day
#             this_month = months[this_date.month-1]
#             this_year = this_date.year
#             extension_dicts[extension]['update'] = str(this_day) + ' ' + \
#                                                     str(this_month) + ' ' + \
#                                                     str(this_year)
#         except:
#             del extension_dicts[extension]['update']





# Figure out what versions of mediawiki this extension works on this
# just looks for a string match of the version. I personally don't
# trust the +,>=,etc... sign people like to use, for example, 1.12+.
# That generally means that they tested it on 1.12, but not the
# versions that came afterwards. Really sketchy is >=1.6. Yeah right!

for extension in extension_dicts.keys():
    if extension_dicts[extension].has_key('mediawiki'):
        supported_versions = []
        version_text = extension_dicts[extension]['mediawiki']
        # TODO: this will break if mw goes past 1.20 or into 2.x
        for version in xrange(2,20): 
            this_version = '1.' + str(version)
            if version_text.find(this_version) != -1:
                supported_versions.append(this_version)
        extension_dicts[extension]['mediawiki'] = ', '.join(supported_versions)





##########################################
# Get the creation date of the extension and the last day that the
# extension and its talk page were edited.
##########################################

for extension in extension_dicts.keys():

    this_extension = mw_site.Pages["Extension:" + extension]
    if this_extension.exists: # should never fail!
        this_date = this_extension.touched
        extension_dicts[extension]['lastupdated'] = str(this_date)

        first_edit_date = list(this_extension.revisions())[-1]['timestamp']
        extension_dicts[extension]['created'] = str(first_edit_date)

    this_extension_talk = mw_site.Pages["Extension_talk:" + extension]
    if this_extension_talk.exists:
        this_date = this_extension_talk.touched
        extension_dicts[extension]['lastupdatedtalk'] = str(this_date)








##########################################
# Create main extension matrix output 
##########################################

# Create the entire extension matrix

for extension in extension_dicts:
    print extension
    template = BuildExtensionTemplate(extension_dicts[extension])

    page = smw_site.Pages['Extension:' + extension]
    page.save(template)



exit()






extension_matrix = ''
prefix = 'Extension Matrix'

updated = 'Last updated: ' + \
          datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + ' MST. '

num_listed = 'Listing ' + str(len(extension_dicts)) + \
             ' out of ' + str(len(extensions)) + \
             ' members of [[:Category:Extensions]]<br/>'


extension_matrix = updated + num_listed + '\n'
extension_matrix += '== Entire Extension Matrix ==\n'
extension_matrix += '* [[' + prefix + '/AllExtensions|View all extensions]] (very large!)\n'



