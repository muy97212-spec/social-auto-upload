import unittest
import sys
import types
from unittest.mock import patch


def install_uploader_stubs():
    modules = {
        "uploader.douyin_uploader.main": {"DouYinVideo": object},
        "uploader.ks_uploader.main": {"KSVideo": object},
        "uploader.tencent_uploader.main": {"TencentVideo": object},
        "uploader.xiaohongshu_uploader.main": {"XiaoHongShuVideo": object},
    }
    for name, attrs in modules.items():
        module = types.ModuleType(name)
        for attr_name, value in attrs.items():
            setattr(module, attr_name, value)
        sys.modules.setdefault(name, module)


class KuaishouBackendCoverTests(unittest.TestCase):
    def test_post_video_ks_passes_thumbnail_to_uploader(self):
        install_uploader_stubs()
        from myUtils.postVideo import post_video_ks

        with patch("myUtils.postVideo.KSVideo") as video_cls, patch("myUtils.postVideo.asyncio.run"):
            video_cls.return_value.main.return_value = object()

            post_video_ks(
                "标题",
                ["demo.mp4"],
                ["AI"],
                ["kuaishou.json"],
                thumbnail_path="/tmp/cover.png",
            )

        self.assertEqual(video_cls.call_args.kwargs["thumbnail_path"], "/tmp/cover.png")


if __name__ == "__main__":
    unittest.main()
