# core/context_processors.py

from django.utils.translation import get_language


def language_context(request):
    """
    Add language-related context variables to templates.
    Provides consistent language toggle functionality.
    """
    current_language = get_language() or 'ar'  # Default to Arabic if not set

    # Set the opposite language and its name
    if current_language == 'ar':
        opposite_language = 'en'
        opposite_language_name = 'English'
    else:
        opposite_language = 'ar'
        opposite_language_name = 'العربية'

    # Clean the path to remove language prefix if present
    path = request.path
    if path.startswith('/en/'):
        path = path[3:] or '/'
    elif path.startswith('/ar/'):
        path = path[3:] or '/'

    # If the path is empty or just '/', make sure it's '/' to avoid 404 errors
    if not path:
        path = '/'
    elif not path.startswith('/'):
        path = '/' + path

    return {
        'current_language': current_language,
        'opposite_language': opposite_language,
        'opposite_language_name': opposite_language_name,
        'clean_path': path,  # Path without language prefix
    }