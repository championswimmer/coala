import functools
import os

from coalib.bears.BEAR_KIND import BEAR_KIND
from coalib.collecting.Importers import iimport_objects
from coalib.misc.Decorators import yield_once
from coalib.output.printers.LOG_LEVEL import LOG_LEVEL
from coalib.parsing.Globbing import iglob, fnmatch


def _get_kind(bear_class):
    try:
        return bear_class.kind()
    except NotImplementedError:
        return None


def _import_bears(file_path, kinds):
    # recursive imports:
    for bear_list in iimport_objects(file_path,
                                     names='__additional_bears__',
                                     types=list):
        for bear_class in bear_list:
            if _get_kind(bear_class) in kinds:
                yield bear_class
    # normal import
    for bear_class in iimport_objects(file_path,
                                      attributes='kind',
                                      local=True):
        if _get_kind(bear_class) in kinds:
            yield bear_class


@yield_once
def icollect(file_paths):
    """
    Evaluate globs in file paths and return all matching files.

    :param file_paths:  file path or list of such that can include globs
    :return:            iterator that yields tuple of path of a matching file,
                        the glob where it was found
    """
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    for file_path in file_paths:
        for match in iglob(file_path):
            yield match, file_path


def collect_files(file_paths, log_printer, ignored_file_paths=None,
                  limit_file_paths=None):
    """
    Evaluate globs in file paths and return all matching files

    :param file_paths:         file path or list of such that can include globs
    :param ignored_file_paths: list of globs that match to-be-ignored files
    :param limit_file_paths:   list of globs that the files are limited to
    :return:                   list of paths of all matching files
    """
    if ignored_file_paths:
        ignore_fnmatch = functools.partial(fnmatch, patterns=ignored_file_paths)
    else:
        ignore_fnmatch = lambda x: False  # Never ignored
    if limit_file_paths:
        limit_fnmatch = functools.partial(fnmatch, patterns=limit_file_paths)
    else:
        limit_fnmatch = lambda x: True  # Always in the limit_files
    valid_files = list(filter(
        lambda x: (os.path.isfile(x[0]) and not ignore_fnmatch(x[0]) and
                   limit_fnmatch(x[0])),
        icollect(file_paths)))

    if valid_files:
        collected_files, file_globs_with_files = zip(*valid_files)
    else:
        collected_files, file_globs_with_files = [], []
    empty_file_globs = set(file_paths) - set(file_globs_with_files)
    for glob in empty_file_globs:
        log_printer.warn("No files matching '{}' were found.".format(glob))

    return list(collected_files)


def collect_dirs(dir_paths, ignored_dir_paths=None):
    """
    Evaluate globs in directory paths and return all matching directories

    :param dir_paths:         file path or list of such that can include globs
    :param ignored_dir_paths: list of globs that match to-be-ignored dirs
    :return:                  list of paths of all matching directories
    """
    if ignored_dir_paths:
        ignore_fnmatch = functools.partial(fnmatch, patterns=ignored_dir_paths)
    else:
        ignore_fnmatch = lambda x: False  # Never ignored
    valid_dirs = list(filter(
        lambda x: os.path.isdir(x[0]) and not ignore_fnmatch(x[0]),
        icollect(dir_paths)))
    if valid_dirs:
        collected_dirs, dummy = zip(*valid_dirs)
        return list(collected_dirs)
    else:
        return []


@yield_once
def icollect_bears(bear_dirs, bear_globs, kinds, log_printer):
    """
    Collect all bears from bear directories that have a matching kind.

    :param bear_dirs:   directory name or list of such that can contain bears
    :param bear_globs:  globs of bears to collect
    :param kinds:       list of bear kinds to be collected
    :param log_printer: log_printer to handle logging
    :return:            iterator that yields a tuple with bear class and
                        which bear_glob was used to find that bear class.
    """
    for bear_dir, dir_glob in filter(lambda x: os.path.isdir(x[0]),
                                     icollect(bear_dirs)):
        for bear_glob in bear_globs:
            for matching_file in iglob(
                    os.path.join(bear_dir, bear_glob + '.py')):

                try:
                    for bear in _import_bears(matching_file, kinds):
                        yield bear, bear_glob
                except BaseException as exception:
                    log_printer.log_exception(
                        "Unable to collect bears from {file}. Probably the "
                        "file is malformed or the module code raises an "
                        "exception.".format(file=matching_file),
                        exception,
                        log_level=LOG_LEVEL.WARNING)


def collect_bears(bear_dirs, bear_globs, kinds, log_printer):
    """
    Collect all bears from bear directories that have a matching kind
    matching the given globs.

    :param bear_dirs:   directory name or list of such that can contain bears
    :param bear_globs:  globs of bears to collect
    :param kinds:       list of bear kinds to be collected
    :param log_printer: log_printer to handle logging
    :return:            tuple of list of matching bear classes based on kind.
                        The lists are in the same order as `kinds`
    """
    bears_found = tuple([] for i in range(len(kinds)))
    bear_globs_with_bears = set()
    for bear, glob in icollect_bears(bear_dirs, bear_globs, kinds, log_printer):
        index = kinds.index(_get_kind(bear))
        bears_found[index].append(bear)
        bear_globs_with_bears.add(glob)

    empty_bear_globs = set(bear_globs) - set(bear_globs_with_bears)
    for glob in empty_bear_globs:
        log_printer.warn("No bears were found matching '{}'.".format(glob))

    return bears_found


def collect_all_bears_from_sections(sections, log_printer):
    """
    Collect all kinds of bears from bear directories given in the sections.

    :param bear_dirs:   directory name or list of such that can contain bears
    :param log_printer: log_printer to handle logging
    """
    local_bears = {}
    global_bears = {}
    for section in sections:
        bear_dirs = sections[section].bear_dirs()
        local_bears[section], global_bears[section] = collect_bears(
            bear_dirs,
            ["**"],
            [BEAR_KIND.LOCAL, BEAR_KIND.GLOBAL],
            log_printer)
    return local_bears, global_bears
