import csv

from robot.api import logger

from .base_handler import BaseHandler
from .errors import LocustHandlerException, SubprocessException
from .utils import run_command_line, validate_path


class LocustHandler(BaseHandler):

    def run_locust(self, result_file, command, check_return_code=False, failure_percentage=None, **env):
        '''Run the Locust load testing tool via ``command``.

        ``result_file`` is the path rmkbridge will read after Locust finishes.
        Craft your ``command`` to write its stats CSV to exactly that path
        (use Locust's ``--csv`` flag and derive the ``_stats.csv`` filename).

        ``command`` is a shell string executed in a subprocess.

        ``check_return_code`` — set to ``True`` while debugging to treat a
        non-zero exit code as a failure. Leave it off for normal use: Locust
        exits non-zero when requests fail, which would swallow real results.

        ``failure_percentage`` is an optional override for the failure threshold. If not provided, the handler will use the value from its configuration (defaulting to 0 if not set). This allows you to specify a different threshold for this particular run.

        Extra keyword arguments are forwarded as environment variables to the
        subprocess.
        '''
        try:
            output = run_command_line(command, check_return_code, **env)
        except SubprocessException as e:
            raise LocustHandlerException(e)
        logger.info(output)
        logger.info(f'Result file: {result_file}')
        return result_file, failure_percentage

    def parse_results(self, result_file, failure_percentage=None):
        effective_threshold = failure_percentage if failure_percentage is not None else self._failure_threshold()
        threshold = min(effective_threshold, 100)
        return self._transform_tests(validate_path(result_file).resolve(), threshold)

    def _transform_tests(self, file, threshold):
        test_cases = []
        with open(file, newline='') as csvfile:
            for row in csv.DictReader(csvfile):
                if row['Type'] == 'None':
                    continue
                failure_count = int(row['Failure Count'])
                request_count = int(row['Request Count'])
                actual_pct = (failure_count / request_count) * 100 if request_count > 0 else 0
                test_cases.append({
                    'name': f"{row['Type']} requests to {row['Name']}",
                    'keywords': [{
                        'name': f"{row['Type']} {row['Name']}",
                        'pass': actual_pct <= threshold,
                        'messages': [f'{k}: {v}' for k, v in row.items()],
                    }],
                })
        return {
            'name': 'Locust Scenario',
            'tags': self._tags,
            'tests': test_cases,
        }
    
    def _failure_threshold(self):
        pct = int(self._config.get('failure_percentage', 0))
        if pct > 100:
            logger.info('failure_percentage capped at 100')
            return 100
        return pct    