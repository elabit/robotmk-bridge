import xml.etree.ElementTree as ET
from collections import defaultdict

from robot.api import logger

from .base_handler import BaseHandler
from .errors import SubprocessException, ToscaExtHandlerException
from .utils import run_command_line, validate_path


class ToscaExtHandler(BaseHandler):

    def run_tosca_ext(self, result_file, command, check_return_code=False, **env):
        '''Run Tricentis Tosca via ``command`` and return the path to its XML report.

        ``result_file`` is the path of the ``XMLReport_Extended`` XML file that
        Tosca writes after execution.  Point your Tosca CLI at that path and
        pass it here so rmkbridge knows where to look.

        ``command`` is a shell string executed in a subprocess.

        ``check_return_code`` — set to ``True`` while debugging to treat a
        non-zero exit code as a failure.

        Extra keyword arguments are forwarded as environment variables to the
        subprocess.
        '''
        try:
            output = run_command_line(command, check_return_code, **env)
        except SubprocessException as e:
            raise ToscaExtHandlerException(e)
        logger.info(output)
        logger.info(f'Result file: {result_file}')
        return result_file

    def parse_results(self, result_file):
        return self._transform_tests(validate_path(result_file).resolve())

    def _transform_tests(self, file):
        root = ET.parse(file).getroot()
        nodes = self._index_nodes(root)

        exec_list = nodes['execution_lists'][0]
        list_surr = exec_list['SurrogateNum']
        list_name = exec_list['Name']

        entries_by_folder = defaultdict(list)
        for entry in nodes['execution_entries']:
            if entry['ParentSurrogateNum'] != list_surr:
                continue
            folder = self._subfolder(entry['NodePath'], list_name)
            entries_by_folder[folder].append(entry)

        suites = []
        for folder, entries in entries_by_folder.items():
            tests = [
                self._build_test(entry, nodes)
                for entry in entries
            ]
            suites.append({'name': folder, 'tests': tests})

        return {
            'name': list_name,
            'tags': self._tags,
            'suites': suites,
        }

    def _index_nodes(self, root):
        execution_lists = []
        execution_entries = []
        log_by_entry = {}
        steps_by_log = defaultdict(list)
        tsv_by_step = defaultdict(list)

        for child in root:
            tag = child.tag
            if tag not in ('ExecutionList', 'ExecutionEntries', 'ActualLog',
                           'TestStep', 'TestStepValue'):
                continue
            data = {c.tag: (c.text or '') for c in child}
            obj_type = data.get('ObjectType', '')

            if tag == 'ExecutionList':
                execution_lists.append(data)
            elif tag == 'ExecutionEntries':
                execution_entries.append(data)
            elif tag == 'ActualLog':
                log_by_entry[data['ParentSurrogateNum']] = data
            elif tag == 'TestStep' and obj_type == 'ExecutionXTestStepLog':
                steps_by_log[data['ParentSurrogateNum']].append(data)
            elif tag == 'TestStepValue':
                tsv_by_step[data['ParentSurrogateNum']].append(data)

        return {
            'execution_lists': execution_lists,
            'execution_entries': execution_entries,
            'log_by_entry': log_by_entry,
            'steps_by_log': steps_by_log,
            'tsv_by_step': tsv_by_step,
        }

    def _subfolder(self, node_path, list_name):
        parts = node_path.split('/')
        try:
            el_idx = parts.index('ExecutionLists')
            list_idx = el_idx + 1
            if parts[list_idx] == list_name and list_idx + 2 < len(parts):
                return parts[list_idx + 1]
        except (ValueError, IndexError):
            pass
        return list_name

    def _build_test(self, entry, nodes):
        log = nodes['log_by_entry'].get(entry['SurrogateNum'])
        log_surr = log['SurrogateNum'] if log else None
        steps = nodes['steps_by_log'].get(log_surr, []) if log_surr else []

        if steps:
            keywords = [self._build_keyword(step, nodes['tsv_by_step']) for step in steps]
        else:
            pass_val = (log['Result'] == 'Passed') if log else (entry['ActualResult'] == 'Passed')
            keywords = [{'name': entry['Name'], 'pass': pass_val, 'messages': []}]

        return {'name': entry['Name'], 'keywords': keywords}

    def _build_keyword(self, step, tsv_by_step):
        messages = [m for m in (step.get('LogInfo'), step.get('Detail')) if m]
        kw = {
            'name': step['Name'],
            'pass': step['Result'] == 'Passed',
            'messages': messages,
            'elapsed': self._parse_ms(step.get('Duration', '0')),
        }
        tsvs = tsv_by_step.get(step['SurrogateNum'], [])
        if tsvs:
            kw['keywords'] = [self._build_tsv_keyword(tsv) for tsv in tsvs]
        return kw

    def _build_tsv_keyword(self, tsv):
        messages = [
            f"Value: {tsv['Value']}" for _ in [1] if tsv.get('Value')
        ] + [
            f"UsedValue: {tsv['UsedValue']}" for _ in [1] if tsv.get('UsedValue')
        ]
        return {
            'name': tsv['Name'],
            'pass': True,
            'messages': messages,
        }

    def _parse_ms(self, duration_str):
        try:
            return float(duration_str.replace(',', '.'))
        except (ValueError, AttributeError):
            return 0.0
