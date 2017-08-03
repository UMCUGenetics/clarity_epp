from __future__ import print_function
"""Clarity epp utility functions and classes."""

import logging
import sys
import os
import pkg_resources
from pkg_resources import DistributionNotFound
from shutil import copy
from requests import HTTPError
from genologics.entities import Artifact
from logging.handlers import RotatingFileHandler
import csv


class EppLogger(object):
    """
    Context manager for logging module useful for EPP script execution.

    Copied from: https://github.com/SciLifeLab/genologics/blob/master/genologics/epp.py
    Johannes Alneberg, Science for Life Laboratory, Stockholm, Sweden.
    Copyright (C) 2013 Johannes Alneberg

    Modified to get rid of configuration bug. See https://github.com/SciLifeLab/genologics/issues/201


    This context manager (CM) automatically logs what script that is executed,
    with what parameters it was executed and what version (including) commit
    hash of the genologics package used. Since EPP scripts are often ran
    automatically by the genologics LIMS client, the stdout and stderr is
    captured and logged within this CM. Stderr is duplicated so that the
    last line can be shown in the GUI. In order to track multiple runs
    of the same process from the genologics LIMS GUI, the previous log
    files can be prepended. Also a main log file can be used that is
    supposed to be common for all scripts executed on the server.
    """

    PACKAGE = 'genologics'

    def __enter__(self):
        logging.info('Executing file: {0}'.format(sys.argv[0]))
        logging.info('with parameters: {0}'.format(sys.argv[1:]))
        try:
            logging.info('Version of {0}: '.format(self.PACKAGE) + pkg_resources.require(self.PACKAGE)[0].version)
        except DistributionNotFound as e:
            logging.error(e)
            logging.error(('Make sure you have the {0} package installed').format(self.PACKAGE))
            sys.exit(-1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If no exception has occured in block, turn off logging.
        if not exc_type:
            logging.shutdown()
            sys.stderr = self.saved_stderr
            sys.stdout = self.saved_stdout
        # Do not repress possible exception
        return False

    def __init__(self, log_file=None, level=logging.INFO, lims=None, prepend=False, main_log=None):
        """Initialize the logger with custom settings.

        Arguments:
        log_file  -- file to write individual log to

        Keyword Arguments:
        level   -- Logging level, default logging.INFO
        lims    -- Lims instance, needed for prepend to work
        prepend -- If True, prepend old log file to new, requires lims
        """
        self.lims = lims
        self.log_file = log_file
        self.level = level
        self.prepend = prepend

        if prepend and self.log_file:
            self.prepend_old_log()

        # Loggers that will capture stdout and stderr respectively
        stdout_logger = logging.getLogger('STDOUT')
        self.slo = self.StreamToLogger(stdout_logger, logging.INFO)
        self.saved_stdout = sys.stdout
        sys.stdout = self.slo

        stderr_logger = logging.getLogger('STDERR')
        self.saved_stderr = sys.stderr
        # Duplicate stderr stream to log
        self.sle = self.StreamToLogger(stderr_logger, logging.INFO, self.saved_stderr)
        sys.stderr = self.sle

        # Root logger with filehandler(s)
        self.logger = logging.getLogger()
        self.logger.setLevel(self.level)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
        if self.log_file:
            individual_fh = logging.FileHandler(self.log_file, mode='a')
            individual_fh.setFormatter(formatter)
            self.logger.addHandler(individual_fh)

        if main_log:
            # Rotating file handler, that will create up to 10 backup logs,
            # each no bigger than 100MB.
            main_fh = RotatingFileHandler(main_log, mode='a', maxBytes=1e8, backupCount=10)
            main_fh.setFormatter(formatter)
            self.logger.addHandler(main_fh)
        else:
            self.logger.warning('No main log file found.')

    def prepend_old_log(self, external_log_file=None):
        """
        Prepend the old log to the new log.

        The location of the old log file is retrieved through the REST api.
        In order to work, the script should be executed on the LIMS server
        since the location on the disk is parsed out from the sftp string
        and then used for local copy of file.

        This method does not use logging since that could mess up the
        logging settings, instead warnings are printed to stderr.
        """
        if external_log_file:
            log_file_name = external_log_file
        else:
            log_file_name = self.log_file

        local_log_path = os.path.join(os.getcwd(), log_file_name)
        if not os.path.isfile(local_log_path):
            try:
                log_artifact = Artifact(self.lims, id=log_file_name)
                log_artifact.get()
                if log_artifact.files:
                    log_path = log_artifact.files[0].content_location.split(
                        self.lims.baseuri.split(':')[1])[1]
                    copy(log_path, local_log_path)
                    with open(local_log_path, 'a') as f:
                        f.write('='*80+'\n')
            except HTTPError:  # Probably no artifact found, skip prepending
                print(('No log file artifact found for id: {0}').format(log_file_name), file=sys.stderr)
            except IOError as e:  # Probably some path was wrong in copy
                print(('Log could not be prepended, make sure {0} and {1} are proper paths.').format(log_path, log_file_name), file=sys.stderr)
                raise e

    class StreamToLogger(object):
        """
        Fake file-like stream object that redirects writes to a logger instance.

        source:
        http://www.electricmonk.nl/log/2011/08/14/
        redirect-stdout-and-stderr-to-a-logger-in-python/
        """

        def __init__(self, logger, log_level=logging.INFO, stream=None):
            self.logger = logger
            self.log_level = log_level
            self.linebuf = ''
            self.stream = stream

        def write(self, buf):
            if self.stream:
                self.stream.write(buf)
            for line in buf.rstrip().splitlines():
                self.logger.log(self.log_level, line.rstrip())


class ReadResultFiles():
    """
    Class to read pars different kinds of result files from a process.

    The class stores the parsed content of all shared result files in a
    dictionary 'shared_files'. The data is parsed as lists of lists.
    """

    def __init__(self, process):
        self.process = process
        self.shared_files = self._pars_file('SharedResultFile')
        self.perinput_files = self._pars_file('ResultFile')

    def get_file_path(self, artifact):
        if len(artifact.files) > 0:
            file = artifact.files[0]
            file_path = file.content_location.split('scilifelab.se')[1]
            if len(file_path.split('.')) > 1:
                return file_path
        return None

    def _pars_file(self, output_type):
        """Read a csv or txt into a list of lists, where sub lists are lines of the csv."""
        outs = self.process.all_outputs()
        outarts = [a for a in outs if a.output_type == output_type]
        parsed_files = {}
        for outart in outarts:
            file_path = self.get_file_path(outart)
            if file_path:
                of = open(file_path, 'r')
                file_ext = file_path.split('.')[-1]
                if file_ext == 'csv':
                    pf = [row for row in csv.reader(of.read().splitlines())]
                    parsed_files[outart.name] = pf
                elif file_ext == 'txt':
                    pf = [row.strip().strip('\\').split('\t') for row in of.readlines()]
                    parsed_files[outart.name] = pf
                of.close()
        return parsed_files

    def format_file(self, parsed_file, name='', first_header=None, header_row=None, root_key_col=0, find_keys=[]):
        """Function to format a parsed csv or txt file.

        Arguments and Output:
            parsed_file     A list of lists where sublists are rows of the csv.
            name            Name of parsed file.
            first_header    First column of the heather section in the file.
                            default value is 'None'
            root_key_col    If you want the root keys to be given by some other
                            column than the first one, set root_key_col to the
                            column number.
            header_row      Instead of specifying first_header you can choose
                            from what line to reed by setting header_row to the
                            row number where you want to start reading.
            find_keys       List of row names to look for. Will exclude all
                            others.
            file_info       Dict of dicts. Keys of root dict are the first
                            column in the csv starting from the line after the
                            heather line. Keys of sub dicts are the columns of
                            the heather line.
        """
        file_info = {}
        keys = []
        error_message = ''
        duplicated_lines = []
        exeptions = ['Sample', 'Fail', '']
        if type(first_header) is not list:
            if first_header:
                first_header = [first_header]
            else:
                first_header = []
        for row, line in enumerate(parsed_file):
            if keys and len(line) == len(keys):
                root_key = line[root_key_col]
                cond1 = find_keys == [] and root_key not in exeptions
                cond2 = root_key in find_keys
                if root_key in file_info:
                    duplicated_lines.append(root_key)
                elif (cond1 or cond2):
                    file_info[root_key] = {}
                    if not duplicated_lines:
                        for col in range(len(keys)):
                            if keys[col] != '':
                                file_info[root_key][keys[col]] = line[col]
                            elif keys[col-1] != '':
                                tupl = (file_info[root_key][keys[col-1]], line[col])
                                file_info[root_key][keys[col-1]] = tupl

            head = line[root_key_col] if len(line) > root_key_col else None
            if first_header and head in first_header:
                keys = line
            elif header_row and row == header_row:
                keys = line
        if duplicated_lines:
            error_message = ("Row names {0} occurs more than once in file {1}. Fix the file to continue.").format(','.join(duplicated_lines), name)
        if not file_info:
            error_message = error_message + "Could not format parsed file {0}.".format(name)
        if error_message:
            print(error_message, file=sys.stderr)
            sys.exit(-1)
        return file_info
