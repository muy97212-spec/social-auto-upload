import unittest

from uploader.tencent_uploader import main as tencent_main


class FakePublishButton:
    def __init__(self):
        self.click_calls = []

    async def count(self):
        return 1

    async def click(self, **kwargs):
        self.click_calls.append(kwargs)
        if len(self.click_calls) == 1:
            raise TimeoutError("share-card subtree intercepts pointer events")


class FakePage:
    def __init__(self, button):
        self.button = button

    def locator(self, selector):
        self.selector = selector
        return self.button


class TencentPublishClickTests(unittest.IsolatedAsyncioTestCase):
    async def test_publish_button_uses_force_click_when_overlay_intercepts_pointer(self):
        button = FakePublishButton()
        page = FakePage(button)

        clicked = await tencent_main._click_tencent_publish_button(page)

        self.assertTrue(clicked)
        self.assertEqual(page.selector, 'div.form-btns button:has-text("发表")')
        self.assertEqual(button.click_calls, [{}, {"force": True}])


class FakeVideoInput:
    def __init__(self, fail_wait=False):
        self.fail_wait = fail_wait
        self.first = self
        self.files = []

    async def wait_for(self, **kwargs):
        self.wait_kwargs = kwargs
        if self.fail_wait:
            raise TimeoutError('waiting for locator("input[type=\\"file\\"]")')

    async def set_input_files(self, file_path):
        self.files.append(file_path)


class FakeUploadPage:
    def __init__(self):
        self.inputs = [FakeVideoInput(fail_wait=True), FakeVideoInput()]
        self.locator_calls = []
        self.reloads = 0

    def locator(self, selector):
        self.locator_calls.append(selector)
        return self.inputs[min(len(self.locator_calls) - 1, len(self.inputs) - 1)]

    async def reload(self, **kwargs):
        self.reloads += 1
        self.reload_kwargs = kwargs

    async def wait_for_url(self, url, **kwargs):
        self.waited_url = url
        self.wait_url_kwargs = kwargs


class TencentVideoUploadInputTests(unittest.IsolatedAsyncioTestCase):
    async def test_video_file_input_reloads_upload_page_once_when_input_is_late(self):
        page = FakeUploadPage()

        await tencent_main._set_tencent_video_file(page, "/tmp/demo.mp4")

        self.assertEqual(page.locator_calls, ['input[type="file"]', 'input[type="file"]'])
        self.assertEqual(page.reloads, 1)
        self.assertEqual(page.inputs[1].files, ["/tmp/demo.mp4"])


class TencentCookieAuthTests(unittest.TestCase):
    def test_login_landing_url_is_not_authenticated(self):
        self.assertFalse(
            tencent_main._is_tencent_authenticated_url("https://channels.weixin.qq.com/login.html")
        )

    def test_upload_url_is_authenticated(self):
        self.assertTrue(
            tencent_main._is_tencent_authenticated_url(
                "https://channels.weixin.qq.com/platform/post/create"
            )
        )

    def test_platform_landing_url_is_authenticated(self):
        self.assertTrue(
            tencent_main._is_tencent_authenticated_url(
                "https://channels.weixin.qq.com/platform"
            )
        )


class FakeInteractiveLoginPage:
    def __init__(self):
        self.url = "https://channels.weixin.qq.com/login.html"
        self.goto_calls = []
        self.wait_count = 0

    async def goto(self, url, **kwargs):
        self.goto_calls.append(url)
        if len(self.goto_calls) > 1:
            self.url = url

    async def wait_for_timeout(self, timeout):
        self.wait_count += 1
        if self.wait_count == 2:
            self.url = "https://channels.weixin.qq.com/platform"

    async def wait_for_url(self, url, **kwargs):
        self.waited_url = url


class TencentInlineLoginTests(unittest.IsolatedAsyncioTestCase):
    async def test_headed_upload_waits_for_login_and_reuses_same_page(self):
        uploader = tencent_main.TencentBaseUploader(
            publish_date=0,
            account_file="/tmp/tencent-test.json",
            headless=False,
        )
        page = FakeInteractiveLoginPage()

        login_performed = await uploader.open_upload_page(page)

        self.assertTrue(login_performed)
        self.assertEqual(
            page.goto_calls,
            [tencent_main.TENCENT_UPLOAD_URL, tencent_main.TENCENT_UPLOAD_URL],
        )
        self.assertEqual(page.waited_url, tencent_main.TENCENT_UPLOAD_URL)


if __name__ == "__main__":
    unittest.main()
