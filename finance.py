from jsonpath import jsonpath
import efinance as ef
import time
import datetime

a = {"用户":
    [{
        "name": "1",
        "money": 84561.12,
        "quote": [
            {
                "code": "600019",
                "num_all": 200,
                "num_today": 100
            }
        ],
        "buy_list": [
            {
                "is_buy": "true",
                "code": "600019",
                "num": 300,
                "pay_money": 51511,
                "timestep": "2021/11/11 11:11"
            }
        ]
    }]
}


# 判断当前时间是否在两个时间之间
def is_between_time(begin_time, end_time):
    now = time.strftime('%H:%M:%S')
    if begin_time <= now <= end_time:
        # print('当前时间在两个时间之间')
        return True
    else:
        return False


def search_acc(user_name: str, a: dict):
    """
    用户查询自己的资金、交易记录、股票持有情况
    Args:
        user_name:用户名
        a:所有信息

    Returns:flag: 返回true，用户存在，放回false，用户不存在
            money: 用户的资金
            record:用户的交易记录
            stock_hold:股票持有情况
    """
    res = jsonpath(a, '$..name')
    if user_name in res:
        flag = True
        # node为该用户的所有信息
        node = jsonpath(a, f'$..[?(@.name == \'{user_name}\')]')[0]
        # hold为该用户持有的股票代码：列表
        hold = jsonpath(node, '$.quote..code')
        # num_all为每个代码的股票持有的数量：列表
        num_all = jsonpath(node, '$.quote..num_all')
        # money为该用户有的现金数量
        money = jsonpath(node, '$.money')[0]
        # record为该用户的股票交易记录
        record = jsonpath(node, '$.buy_list')[0]
        # stock_hold为该用户所持有的所有股票信息
        stock_hold = jsonpath(node, '$.quote')[0]
        for i in stock_hold:
            if i["num_all"] & i["num_today"] == 0:
                stock_hold.remove(i)
        return flag, money, record, stock_hold
    else:
        flag = False
        return flag, 0, 0, 0


def find_single_price(stock_code: str):
    # 根据股票代码查询当前时刻的股票价格
    df = ef.stock.get_quote_history(stock_code, klt=1)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())[:-3]
    df = df.set_index('日期')
    if is_between_time("09:30:00", "11:30:00"):
        money = df.loc[formatted_time, '开盘']
    elif is_between_time("11:30:00", "13:00:00"):
        formatted_time = datetime.datetime.now().strftime('%Y-%m-%d') + " 11:30"
        money = df.loc[formatted_time, '开盘']
    elif is_between_time("13:00:00", "15:00:00"):
        money = df.loc[formatted_time, '开盘']
    elif is_between_time("15:00:00", "24:00:00"):
        formatted_time = datetime.datetime.now().strftime('%Y-%m-%d') + " 15:00"
        money = df.loc[formatted_time, '开盘']
    else:
        formatted_time = datetime.datetime.now().strftime('%Y-%m-%d') + " 15:00"
    return money


def find_acc_value(user_name: str, a: dict):
    """
    返回账户价值：股票价值加上自身money
    Args:
        user_name: 用户名
        a: 所有信息

    Returns:flag:用户名是否存在
            money:账户价值
    """
    res = jsonpath(a, '$..name')
    if user_name in res:
        flag = True
        # node为该用户的所有信息
        node = jsonpath(a, f'$..[?(@.name == \'{user_name}\')]')[0]
        # hold为该用户持有的股票代码：列表
        hold = jsonpath(node, '$.quote..code')
        # num_all为每个代码的股票持有的数量：列表
        num_all = jsonpath(node, '$.quote..num_all')
        money = jsonpath(node, '$.money')[0]
        for i, j in zip(hold, num_all):
            money += find_single_price(i) * j

        return flag, money
    else:
        return False, 0


def find_single_profit(user_name: str, a: dict, stock_code: str):
    """
    根据用户的用户名和股票代码查看用户单股的收益
    Args:
        user_name: 用户名
        a: 数据
        stock_code: 股票代码

    Returns:flag：用户是否存在
            profit:该股票的收益

    """
    res = jsonpath(a, '$..name')
    if user_name in res:
        # node为该用户的所有信息
        node = jsonpath(a, f'$..[?(@.name == \'{user_name}\')]')[0]
        hold = jsonpath(node, '$.quote..code')
        if stock_code in hold:
            # 现在持有该股票
            flag = True
            # record_buy为该股票购买还是卖出的标记
            record_buy = jsonpath(node, f'$.buy_list[?(@.code == \'{stock_code}\')].is_buy')
            # record为该股票每次购买还是卖出的钱
            record = jsonpath(node, f'$.buy_list[?(@.code == \'{stock_code}\')].pay_money')
            # num_now为该股票目前持有的数量值
            num_now = jsonpath(node, f'$.quote[?(@.code == \'{stock_code}\')].num_all')[0]
            price_now = find_single_price(stock_code) * num_now
            price_before = 0
            for i, j in zip(record_buy, record):
                if i == 'true':
                    price_before += j
                else:
                    price_before -= j
            profit = price_now - price_before
            return flag, profit
        else:
            # 现在未持有该股票
            flag = True
            # record_buy为该股票购买还是卖出的标记
            record_buy = jsonpath(node, f'$.buy_list[?(@.code == \'{stock_code}\')].is_buy')
            # record为该股票每次购买还是卖出的钱
            record = jsonpath(node, f'$.buy_list[?(@.code == \'{stock_code}\')].pay_money')
            price = 0
            for i, j in zip(record_buy, record):
                if i == 'true':
                    price += j
                else:
                    price -= j
            return flag, price
    else:
        flag = False
        return flag, 0


def find_all_profit(user_name: str, a: dict):
    res = jsonpath(a, '$..name')
    if user_name in res:
        flag = True
        # node为该用户的所有信息
        node = jsonpath(a, f'$..[?(@.name == \'{user_name}\')]')[0]
        # record为所有交易记录里面的购买售出标记
        record = jsonpath(node, '$.buy_list[*].is_buy')
        # money为每次交易所花费或获得的钱
        money = jsonpath(node, '$.buy_list[*].pay_money')
        print(money)
        profit = 0
        for i, j in zip(record, money):
            if i == 'true':
                profit -= j
            else:
                profit += j
        # hold为该用户持有的股票代码：列表
        hold = jsonpath(node, '$.quote..code')
        # num_all为每个代码的股票持有的数量：列表
        num_all = jsonpath(node, '$.quote..num_all')
        for i, j in zip(hold, num_all):
            profit += find_single_price(i) * j

        return flag, profit

    else:
        flag = False
        return flag, 0


def buy_stock(user_name: str, a: dict, code: str, num: int):
    """
    购买股票
    Args:
        a:
        user_name:用户名
        a：数据库
        code: 代码
        num: 数量

    Returns:flag:是否购买成功

    """
    flag = True
    res = jsonpath(a, '$..name')
    if user_name in res:
        # node为当前所输入的username的所有信息
        node = jsonpath(a, f'$..[?(@.name == \'{user_name}\')]')[0]
        # 持有的股票代码
        hold = jsonpath(node, '$.quote..code')
        # 每个代码的股票持有的数量
        num_all = jsonpath(node, '$.quote..num_all')
        buy_list = jsonpath(node, '$.buy_list')[0]
        money = jsonpath(node, '$.money')[0]
        if money > find_single_price(code) * num:
            flag = True
            quote = node["quote"]
            buy_l = {"is_buy": "true",
                     "code": code,
                     "num": num,
                     "pay_money": find_single_price(code) * num,
                     "timestep": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())[:-3]
                     }
            node["buy_list"].append(buy_l)
            money = money - find_single_price(code) * num
            node["money"] = money
            node["buy_list"] = buy_list
            if code in hold:
                for i in quote:
                    if i["code"] == code:
                        i["num_all"] += num
                        i["num_today"] = num

            else:
                b = {"code": code,
                     "num_all": num,
                     "num_today": num}
                node["quote"].append(b)

        else:
            flag = False

    return flag


def sell_stock(user_name: str, a: dict, code: str, num: int):
    # money 为当前现金，record 为当前交易记录，stock_hold 为当前股票持有情况
    res = jsonpath(a, '$..name')
    if user_name in res:
        # node为当前所输入的username的所有信息
        node = jsonpath(a, f'$..[?(@.name == \'{user_name}\')]')[0]
        flag, money1, record2, stock_hold = search_acc(user_name, a)
        hold = jsonpath(node, '$.quote..code')
        if code not in hold:
            return False
        else:
            num_all = jsonpath(node,f'$.quote[?(@.code == \'{code}\')]')[0]["num_all"]
            num_today = jsonpath(node,f'$.quote[?(@.code == \'{code}\')]')[0]["num_today"]
            print(num_all)
            print(num_today)
            if num > num_all - num_today:
                return False
            else:
                buy_list = jsonpath(node, '$.buy_list')[0]
                money = jsonpath(node, '$.money')[0]
                buy_l = {"is_buy": "false",
                         "code": code,
                         "num": num,
                         "pay_money": find_single_price(code) * num,
                         "timestep": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())[:-3]
                         }
                node["buy_list"].append(buy_l)
                money = money + find_single_price(code) * num
                node["money"] = money
                node["buy_list"] = buy_list
                quote = node["quote"]
                if code in hold:
                    for i in quote:
                        if i["code"] == code:
                            i["num_all"] -= num
                return True
    else:
        return False
