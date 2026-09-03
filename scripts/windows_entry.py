"""冻结程序的入口：保留退出码，并兼容 Windows 多进程启动。"""

from multiprocessing import freeze_support


if __name__ == "__main__":
    freeze_support()

    from qt_dicom_viewer.app import main

    raise SystemExit(main())
