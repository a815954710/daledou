import os
import time

from schedule import every, repeat, run_pending

from .config import Config
from .daledou import TaskSchedule
from .session import SessionManager
from .utils import (
    DLD_EXECUTION_MODE_ENV,
    DateTime,
    ExecutionMode,
    Input,
    ModulePath,
    TaskType,
    TimingConfig,
    parse_cookie,
    print_separator,
)


def _execute_one() -> None:
    """执行第一轮任务"""
    TaskSchedule.execute(TaskType.ONE, ModulePath.ONE)


def _execute_two() -> None:
    """执行第二轮任务"""
    TaskSchedule.execute(TaskType.TWO, ModulePath.TWO)


@repeat(every().day.at(TimingConfig.ONE_EXECUTION_TIME, DateTime.SHANGHAI_TZ))
def job_one() -> None:
    """每天定时执行第一轮任务（上海时区）"""
    _execute_one()
    TimingConfig.print_schedule_info()
    print_separator()


@repeat(every().day.at(TimingConfig.TWO_EXECUTION_TIME, DateTime.SHANGHAI_TZ))
def job_two() -> None:
    """每天定时执行第二轮任务（上海时区）"""
    _execute_two()
    TimingConfig.print_schedule_info()
    print_separator()


def _execute_timing() -> None:
    """运行定时任务"""
    if not Config.list_all_qq_numbers():
        return

    TimingConfig.print_schedule_info()
    print_separator()

    while True:
        run_pending()
        time.sleep(1)


class CLIHandler:
    """命令行处理器"""

    def __init__(self):
        self.tasks = {}
        self._setup_tasks()

    def _setup_tasks(self) -> None:
        """设置可用任务"""
        self.tasks = {
            "一键执行": self.one_click_execute,
            "执行任务": self.execute_tasks,
            "调试任务": self.execute_debug,
            "管理账号": self.manage_account,
        }

    def execute_tasks(self) -> None:
        """运行任务 - 包含所有任务类型和执行模式选择"""
        modes = {
            "顺序执行": ExecutionMode.SEQUENTIAL,
            "并发执行": ExecutionMode.CONCURRENT,
        }

        print("💡 执行模式说明：")
        print("• 顺序执行：账号依次执行")
        print("• 并发执行：多账号同时执行（最多5个）\n")

        mode = Input.select("请选择执行模式：", list(modes))
        if mode is None:
            return

        # 任务类型选择
        tasks = {
            "定时任务": _execute_timing,
            "第一轮任务": _execute_one,
            "第二轮任务": _execute_two,
        }

        os.environ[DLD_EXECUTION_MODE_ENV] = modes[mode]
        print(f"已设置为{mode}")
        print_separator()

        print("💡 任务类型说明：")
        print(
            f"• 第一轮包含绝大部分日常任务，建议 {TimingConfig.ONE_EXECUTION_TIME} 后执行"
        )
        print(f"• 第二轮是收尾日常任务，建议 {TimingConfig.TWO_EXECUTION_TIME} 后执行")
        print("• 定时任务是定时执行第一、二轮任务\n")

        task = Input.select("请选择任务：", list(tasks))
        if task is None:
            return

        tasks[task]()

    def one_click_execute(self) -> None:
        """一键执行：顺序执行第一轮任务+第二轮任务"""
        # 固定为顺序执行
        os.environ[DLD_EXECUTION_MODE_ENV] = ExecutionMode.SEQUENTIAL

        print("💡 一键执行说明：")
        print("• 等价于：执行任务 → 顺序执行 → 第一轮任务+第二轮任务")
        print_separator()

        # 按顺序执行第一轮和第二轮任务
        _execute_one()
        _execute_two()

    def execute_debug(self) -> None:
        """调试任务 - 单账号单任务执行"""
        task_map = {
            "其它任务": (TaskType.OTHER, ModulePath.OTHER),
            "第一轮任务": (TaskType.ONE, ModulePath.ONE),
            "第二轮任务": (TaskType.TWO, ModulePath.TWO),
        }

        print("💡 调试模式：每次仅执行单个账号的单个任务")
        print("💡 支持热重载：修改任务代码后无需重启程序")
        print("💡 重载模块：common、one、two、other\n")

        task = Input.select("请选择调试任务：", list(task_map))
        if task is None:
            return

        task_type, module_path = task_map[task]
        TaskSchedule.execute_debug(task_type, module_path)

    def manage_account(self) -> None:
        """管理账号 - 创建或更新账号配置"""
        print("💡 操作说明：")
        print("• 添加新账号会创建对应的配置文件")
        print("• 如果账号已存在，则仅更新Cookie和Token，保留其它所有配置\n")

        print("💡 获取大乐斗Cookie流程：")
        print("1. 应用商店下载Via浏览器")
        print("2. 将Via设为默认浏览器")
        print("3. 使用Via一键登录文字版大乐斗")
        print("4. 等待3秒后点击Via左上角✓")
        print("5. 再点击查看Cookies")
        print_separator()

        while True:
            cookie = Input.text("请输入大乐斗Cookie：")
            if cookie is None:
                break

            ck = parse_cookie(cookie)
            if not ck:
                print("\n❌ Cookie格式不正确")
                print_separator()
                continue

            session = SessionManager.create_verified_session(ck)
            if session is None:
                print("\n❌ Cookie无效或验证失败")
                print_separator()
                continue
            print_separator()

            is_update_push_token = Input.select(
                "是否更新pushplus推送加token？", ["yes", "no"]
            )
            if is_update_push_token is None:
                break
            elif is_update_push_token == "yes":
                push_token = Input.text("请输入pushplus推送加token：")
                if push_token is None:
                    break
                print_separator()
            elif is_update_push_token == "no":
                push_token = ""

            qq = ck["newuin"]
            account_config_path = Config.save_account_config(
                f"{qq}.yaml", cookie, push_token
            )
            print(f"✅ 账号 {qq} 配置成功！")
            print(f"📁 账号配置文件：{account_config_path}\n")
            print_separator()


def run_serve() -> None:
    """运行主服务"""
    handler = CLIHandler()
    qq_numbers = Config.list_all_qq_numbers()

    print_separator()
    if not qq_numbers:
        print("❌ 没有找到账号配置文件")
        print("💡 请先使用「管理账号」功能添加账号")
        print("💡 禁用账号只需将对应配置文件移出 config/accounts 目录即可\n")
        available_tasks = {"管理账号": handler.manage_account}
    else:
        for qq in qq_numbers:
            Config.load_account_config(f"{qq}.yaml")

        print("✅ 配置文件检查完成")
        print("   - 账号配置格式正确")
        print("   - 全局配置格式正确")
        print("   - 合并配置已生成")
        print_separator()
        available_tasks = handler.tasks

    task = Input.select("请选择任务：", list(available_tasks))
    if task is None:
        return

    available_tasks[task]()
