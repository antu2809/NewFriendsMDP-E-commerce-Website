"""
A template tag that creates menu items that introspect the view 
they point to, only displaying those that the currently logged
in user can access. It also marks the currently selected item as
'active' with a css class.

Usage:

    {% menu_item "url:view_name" "Menu Title" %}

If you prefix view_name with url, as shown, then it will use reverse()
to find the view.  Otherwise, it assumes you have entered the actual
url.

A third, optional argument is a list of css classes that should be
applied to this menu item.

Note: If you have urls like /foo/bar/baz/, and your menu is /foo/bar/,
then this matches the url, and the menu item /foo/bar/ would be selected.
This would mean you can't use {% menu_item '/' 'Home' %}, so I have a
couple of special cases:
    
* the url '/' is handled specially, only an exact match will cause
  it to be marked as active.
* the text 'Menu Title' is compared in a case insensitive fashion
  to the string 'home': if it matches exactly, then it requires an
  exact url match (not just a matching prefix) to be marked as
  active.
    
The logic for determining permission to access a view is pretty simple:
look for any decorators on that view that take a first argument called
`user` or `u`, and call them with the current request.user object. If
any fail, then this user may not access that view.
"""

from django import template
from django.conf import settings
from django.core.urlresolvers import Resolver404, reverse, resolve
from django.utils.itercompat import is_iterable

register = template.Library()

def get_callable_cells(function):
    """
    Iterate through all of the decorators on this function,
    and put those that might be callable onto our callable stack.
    
    Note that we will also include the function itself, as that
    is callable.
    
    This is probably the funkiest introspection code I've ever written in python.
    """
    callables = []
    if not hasattr(function, 'func_closure'):
        if hasattr(function, 'view_func'):
            return get_callable_cells(function.view_func)
    if not function.func_closure:
        return [function]
    for closure in function.func_closure:
        if hasattr(closure.cell_contents, '__call__'):
            # Class-based view does not have a .func_closure attribute.
            # Instead, we want to look for decorators on the dispatch method.
            # We can also look for decorators on a "get" method, if one exists.
            if hasattr(closure.cell_contents, 'dispatch'):
                callables.extend(get_callable_cells(closure.cell_contents.dispatch.__func__))
                if hasattr(closure.cell_contents, 'get'):
                    callables.extend(get_callable_cells(closure.cell_contents.get.__func__))
            elif hasattr(closure.cell_contents, 'func_closure') and closure.cell_contents.func_closure:
                callables.extend(get_callable_cells(closure.cell_contents))
            else:
                callables.append(closure.cell_contents)
    return [function] + callables

def get_tests(function):
    """
    Get a list of callable cells attached to this function that have the first
    parameter named "u" or "user".
    """
    return [
        x for x in get_callable_cells(function)
        if getattr(x, 'func_code', None) and (
            x.func_code.co_varnames[0] in ["user", "u"] or
            (len(x.func_code.co_varnames) > 1 and x.func_code.co_varnames[0] in ['self', 'cls'] and x.func_code.co_varnames[1] in ['u', 'user'])
        )
    ]

def test_view(test, urlconf, user):
    """
    Run a view test. Add in *args, **kwargs if appropriate.
    """
    args = [] if 'args' not in test.func_code.co_varnames else urlconf.args
    kwargs = {} if 'kwargs' not in test.func_code.co_varnames else urlconf.kwargs
    return test(user, *args, **kwargs)

def _get(x, y):
    try:
        return x[y]
    except TypeError:
        return getattr(x, y)
    
def resolve_path(path, context):
    return reduce(_get, path.split('.'), context)
    
class MenuItem(template.Node):
    """
    The template node for generating a menu item.
    """
    def __init__(self, template_file, url, text, classes=None, *url_args, **kwargs):
        """
        template_file : the name of the template that should be used for each
                        menu item. defaults to 'menu/item.html', but you can
                        override this in a new instance of this tag.
        url:            the url or url:view_name that this menu_item should point to.
        text:           the text that this menu_item will display
        classes:        Any CSS classes that should be applied to the item.
        """
        self.always_display = kwargs.pop('always_display', False)
        super(MenuItem, self).__init__()
        self.template_file = template_file or 'menu/item.html'
        self.url = url
        self.url_args = url_args
        self.text = text
        self.classes = classes if classes else ""
        self.icons = []
        if classes:
            self.classes = classes
            if 'icon:' in classes:
                classes = classes.strip("\"'").split(' ')
                for cl in list(classes):
                    if cl.startswith('icon:'):
                        self.icons.append(cl[5:])
                        classes.remove(cl)
                self.classes = '"' + " ".join(classes) +'"'
        self.nodelist = []
        
    def render(self, context):
        """
        At render time, we need to access the context, to get some data that
        is required.
        
        Basically, we need `request` to be in the context, so we can access
        the logged in user.
        """
        if self.url[0] in "\"'":
            url = self.url.strip("'\"")
        else:
            url = self.url
            
        if url.startswith('url:'):
            if self.url_args:
                url_args = [resolve_path(x, context) for x in self.url_args]
                url = reverse(url[4:], args=url_args)
            else:
                url = reverse(url[4:])
        elif url.startswith('http'):
            pass
        else:
            url = resolve_path(url, context)
        
        if self.text[0] in "\"'":
            text = self.text.strip("\"'")
        else:
            text = resolve_path(self.text, context)

        if not self.classes or self.classes[0] in "\"'":
            classes = self.classes.strip("\"'")
        else:
            classes = resolve_path(self.classes, context)
        
        context.render_context[self] = {
            'url': url,
            'text': text,
            'classes': classes,
            'icons': self.icons
        }
        
        local = dict(context.render_context[self])
        
        if 'request' not in context:
            if settings.DEBUG:
                raise template.TemplateSyntaxError("menu_item tag requires 'request' in context")
            return ''
        
        # If it is an absolute URL, we can shortcut.
        if url.startswith('http'):
            self._update_nodelist()
            return self.nodelist.render(template.context.Context(local))
        
        request = context['request']
        
        # To find our current url, look in order at these.
        if 'page_url' in context:
            page_url = context['page_url']
        elif 'flatpage' in context:
            page_url = context['flatpage'].url
        else:
            page_url = request.path
        
        user = request.user
        
        # This is a fairly nasty hack to get around how I have my mod_python (!!!)
        # setup: which sets the SCRIPT_NAME.
        local['url'] = local['url'].replace(request.META.get('SCRIPT_NAME',''), '')
        
        # See if that url is for a valid view.
        try:
            view = resolve(local['url'])
        except Resolver404:
            if settings.DEBUG:
                raise
            return ''
        
        # See if the user passes all tests.
        # Note that any type of Exception will result in a failure.
        try:
            can_view = all([test_view(test, view, user) for test in get_tests(view.func)])
        except Exception:
            if settings.DEBUG:
                raise
            return ''
        
        # If the user can't access the view, this token collapses to an empty string.            
        if not can_view:
            if self.always_display:
                local['classes'] += 'disabled'
                local['url'] = "#"
            else:
                return ''
        
        # Special-case: when the menu-item's url is '/' or text is 'home', then we don't mark
        # it as active unless it's a complete match.
        if page_url.startswith(local['url']):
            if (local['url'] != '/' and local['text'].lower() != 'home') or page_url == local['url']:
                local['classes'] += " active"
        
        self._update_nodelist()
        new_context = template.context.Context(local)
        return self.nodelist.render(new_context)
    
    def _update_nodelist(self):
        # Now import and render the template.
        file_name = self.template_file
        
        # Cache the nodelist within this template file.
        if not self.nodelist:
            from django.template.loader import get_template, select_template
            if isinstance(file_name, template.Template):
                t = file_name
            elif not isinstance(file_name, basestring) and is_iterable(file_name):
                t = select_template(file_name)
            else:
                t = get_template(file_name)
            self.nodelist = t.nodelist
    
    
def base_menu_item(template="menu/item.html", always_display=False):
    """
    The actual template tag.
    """
    def inner(_parser, token):
        error_message = "'menu_item' tag requires at least 2, arguments"
    
        try:
            parts = token.split_contents()
        except ValueError:
            raise template.TemplateSyntaxError(error_message)
        
        if not (3 <= len(parts)):
            raise template.TemplateSyntaxError(error_message)
        
        # parts[0] is the name of the tag.
        return MenuItem(template, *parts[1:], always_display=always_display)
    return inner

register.tag('menu_item', base_menu_item())
register.tag('li_menu_item', base_menu_item('menu/li-item.html'))
register.tag('button_menu_item', base_menu_item('menu/button-item.html'))
register.tag('li_button_menu_item', base_menu_item('menu/li-button-item.html'))
register.tag('li_menu_item_disabled', base_menu_item('menu/li-item.html', True))
