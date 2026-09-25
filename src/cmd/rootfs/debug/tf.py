from src.cmd.utils.result import CommandResult


def cmd_true(args):
    print("0")
    return CommandResult(status=0)


def cmd_false(args):
    print("1")
    return CommandResult(status=1)