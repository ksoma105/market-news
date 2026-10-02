import io
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from unittest.mock import Mock, patch

from scripts.generate_audio import convert, current_issue, generate


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.issue = '2026-10-02-1200'
        folder = self.root / 'docs/narration'
        folder.mkdir(parents=True)
        (folder / (self.issue + '.txt')).write_text('本日の経済ニュースです。', encoding='utf-8')
        (self.root / 'docs/index.html').write_text(
            '<a href="narration/' + self.issue + '.txt">原稿</a>', encoding='utf-8')
        self.env = {'ELEVENLABS_API_KEY': 'test-secret', 'ELEVENLABS_VOICE_ID': 'test-voice'}
        self.convert = Mock(return_value=b'valid-mp3')
        self.validate = Mock(return_value=30.5)

    def run_audio(self, **kwargs):
        return generate(self.root, self.issue, kwargs.pop('env', self.env),
                        kwargs.pop('converter', self.convert), kwargs.pop('validator', self.validate))

    def test_success_saves_mp3_and_status_without_modifying_article(self):
        article = (self.root / 'docs/index.html').read_bytes()
        state = self.run_audio()
        self.assertEqual(state['status'], 'ready')
        self.assertEqual(state['file'], self.issue + '.mp3')
        self.assertEqual((self.root / 'docs/index.html').read_bytes(), article)
        self.assertEqual((self.root / 'docs/audio' / state['file']).read_bytes(), b'valid-mp3')

    def test_duplicate_run_is_not_billed(self):
        self.run_audio()
        self.run_audio()
        self.convert.assert_called_once()

    def test_config_missing_skips_without_calling_api(self):
        state = self.run_audio(env={})
        self.assertEqual(state['reason'], 'configuration_missing')
        self.convert.assert_not_called()

    def test_quota_subscription_and_rate_limits_skip_without_retry(self):
        for code, status, reason in [(401, 'quota_exceeded', 'quota_exceeded'),
                                     (403, 'subscription_required', 'subscription_required'),
                                     (429, 'too_many_concurrent_requests', 'rate_limited')]:
            with self.subTest(status=status):
                path = self.root / 'docs/audio' / (self.issue + '.json')
                path.unlink(missing_ok=True)
                body = json.dumps({'detail': {'status': status, 'message': 'secret test-secret'}}).encode()
                converter = Mock(side_effect=HTTPError('url', code, 'error', {}, io.BytesIO(body)))
                state = self.run_audio(converter=converter)
                self.assertEqual(state['status'], 'skipped')
                self.assertEqual(state['reason'], reason)
                self.assertNotIn('test-secret', path.read_text())
                self.assertFalse((self.root / 'docs/audio' / (self.issue + '.mp3')).exists())
                self.run_audio(converter=converter)
                converter.assert_called_once()

    def test_unknown_403_does_not_assume_subscription_expired(self):
        converter = Mock(side_effect=HTTPError('url', 403, 'error', {}, io.BytesIO(b'{}')))
        self.assertEqual(self.run_audio(converter=converter)['reason'], 'api_error')

    def test_timeout_keeps_article_and_records_skip(self):
        state = self.run_audio(converter=Mock(side_effect=TimeoutError()))
        self.assertEqual(state['reason'], 'timeout')
        self.assertTrue((self.root / 'docs/index.html').exists())

    def test_invalid_audio_is_never_published(self):
        state = self.run_audio(validator=Mock(side_effect=ValueError('invalid')))
        self.assertEqual(state['status'], 'skipped')
        self.assertEqual(list((self.root / 'docs/audio').glob('*.mp3*')), [])
        self.assertEqual(state['failure_stage'], 'validation')
        self.assertTrue((self.root / 'audio-work' / (self.issue + '.mp3')).exists())

    def test_missing_validator_does_not_bill(self):
        with patch('scripts.generate_audio.shutil.which', return_value=None):
            from scripts.generate_audio import validate_audio
            state = self.run_audio(validator=validate_audio)
        self.assertEqual(state['status'], 'skipped')
        self.assertEqual(state['failure_stage'], 'prepare')
        self.convert.assert_not_called()

    def test_new_issue_after_skip_can_generate(self):
        self.run_audio(env={})
        self.issue = '2026-10-02-2200'
        (self.root / 'docs/narration' / (self.issue + '.txt')).write_text('夜のニュースです。', encoding='utf-8')
        self.assertEqual(self.run_audio()['status'], 'ready')

    def test_long_script_is_not_truncated_or_sent(self):
        (self.root / 'docs/narration' / (self.issue + '.txt')).write_text('あ' * 9501, encoding='utf-8')
        self.assertEqual(self.run_audio()['reason'], 'invalid_narration_length')
        self.convert.assert_not_called()

    def test_issue_selected_from_current_narration_not_archive_links(self):
        with (self.root / 'docs/index.html').open('a', encoding='utf-8') as out:
            out.write('<a href="archive/2026-10-02-0600.html">過去号</a>')
        self.assertEqual(current_issue(self.root), self.issue)

    def test_ambiguous_issue_is_rejected(self):
        with (self.root / 'docs/index.html').open('a', encoding='utf-8') as out:
            out.write('<a href="narration/2026-10-02-2200.txt">原稿</a>')
        with self.assertRaises(ValueError):
            current_issue(self.root)

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(ValueError):
            generate(self.root, '../escape', self.env, self.convert, self.validate)

    def test_api_request_uses_eleven_v4_and_japanese(self):
        response = Mock()
        response.headers.get_content_type.return_value = 'audio/mpeg'
        response.read.return_value = b'audio'
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        opener = Mock()
        opener.open.return_value = response
        with patch('scripts.generate_audio.request.build_opener', return_value=opener):
            self.assertEqual(convert('ニュースです。', 'secret', 'voice/id'), b'audio')
        req = opener.open.call_args.args[0]
        body = json.loads(req.data)
        self.assertEqual(body['model_id'], 'eleven_v4')
        self.assertEqual(body['language_code'], 'ja')
        self.assertIn('voice%2Fid', req.full_url)
        self.assertEqual(opener.open.call_args.kwargs['timeout'], 120)


if __name__ == '__main__':
    unittest.main()
