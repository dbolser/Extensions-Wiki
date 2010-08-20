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

# Bring in me subs
from subs import GetExtensionTemplate
from subs import BuildExtensionTemplate
from subs import ParseExtensionTemplate



# Get a 'site' object and login
print 'logging into MW'
mw_site = mwclient.Site('www.mediawiki.org', path='/w/')
mw_site.login(mw_username, mw_password)



# Get a 'site' object and login
print 'logging into SMW'
smw_site = mwclient.Site('extensions.referata.com', path='/w/')
smw_site.login(smw_username, smw_password)



# Get a list of all the pages in the 'all extensions' category
print 'getting a list of extensions from MW'
all_extensions = mw_site.categories["All extensions"]

##Debugging
#all_extensions = mw_site.categories["Semantic MediaWiki extensions"]

## There must be a way to do this...
#print 'got a list of %d extensions from MW' % len(all_extensions)



## These will be removed!
extensions, extension_dicts = {}, {}



def DateFormat(mwdate):
    ## Get the date in 'ISO' format for SMW
    ## http://semantic-mediawiki.org/wiki/Type:Date
    return '%04d-%02d-%02dT%02d:%02d:%02d' % (mwdate.tm_year, mwdate.tm_mon, mwdate.tm_mday, mwdate.tm_hour, mwdate.tm_min, mwdate.tm_sec)





###############################################
# Download the template_text for each extension from MW
# Parse it
# Upload it to SMW
###############################################

print 'doing'

for this_extension in all_extensions:
    try:

        page_name = this_extension.name

        if ':' not in page_name:
            print ''
            print 'ignoring ' + page_name
            continue

        extension_name = page_name.split(':')[1]

        ## Debugging
        print ''
        print extension_name

        # Don't allow subpage extensions
        if '/' in extension_name:
            print 'discarding (subpage) : ' + extension_name
            continue

        # Keep empty vals around to create a list of poorly formatted
        # extensions
        extensions[extension_name] = ''

        ## Debugging
        #if(len(extensions) > 3):
        #    break

        # Extract the page text.
        print 'getting page text'
        try:
            page_text = this_extension.edit()
        except:
            exit('couldnt get page text!')
        
        # Extract the template from the page text.
        print 'getting template text'
        template_text = GetExtensionTemplate(page_text)
        
        if template_text == 0:
            exit('couldnt get template text!')

        # Parse the extension text
        print 'parsing template text'
        extension_dict = ParseExtensionTemplate(template_text)



        ## Grab some significant dates
        print 'grabbing some dates'
        extension_dict['page last updated'] = \
            DateFormat(this_extension.touched)
        extension_dict['page created'] = \
            DateFormat(list(this_extension.revisions())[-1]['timestamp'])

        this_extension_talk = \
            mw_site.Pages["Extension_talk:" + extension_name]

        if this_extension_talk.exists:
            extension_dict['talk page last updated'] = \
                DateFormat(this_extension_talk.touched)



        # TODO:
        extension_dict['name'] = extension_name

#        if 'name' in key:
#            # Sometimes the name field doesn't contain the actual name
#            # of the extension
#            value = extension


        ## Build the new template
        print 'building the new template'
        new_template = BuildExtensionTemplate(extension_dict)

        ## Write the new page
        print 'writing the new page'
        page = smw_site.Pages['Extension:' + extension_name]
        page.save(new_template)

    except:
        # If someone did something stupid, not worth breaking the bot
        print('failed! : ' + extension_name)
        continue


## Done!
exit()








## Page stuff to emulate at some point

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


