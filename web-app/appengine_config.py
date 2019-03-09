from google.appengine.ext import vendor

# Add any libraries installed in the "lib" folder.
vendor.add('lib')

import os
import sys

#on_appengine = os.environ.get('SERVER_SOFTWARE','').startswith('Development')
#if on_appengine and os.name == 'nt':
#    os.name = None
if os.environ.get('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    sys.path.insert(0, 'lib.zip')
else:
    if os.name == 'nt':
        os.name = None
        sys.platform = ''