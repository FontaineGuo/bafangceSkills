## 股票列表
API接口：https://api.biyingapi.com/hslt/list/您的licence
接口说明：获取基础的股票代码和名称，用于后续接口的参数传入。
数据更新：每日16:20
请求频率：1分钟300次 | 包年版1分钟3千次 | 白金版1分钟6千次
返回格式：标准Json格式      [{},...{}]
数据范围样例：
```json
[{"dm":"000001.SZ","mc":"平安银行","jys":"SZ"},{"dm":"000002.SZ","mc":"万 科Ａ","jys":"SZ"}]
```
字段说明：
字段名称	数据类型	字段说明
dm	string	股票代码，如：000001
mc	string	股票名称，如：平安银行
jys	string	交易所，"sh"表示上证，"sz"表示深证

## 实时交易数据
API接口：https://api.biyingapi.com/hsstock/real/time/股票代码/证书您的licence
接口说明：根据《股票列表》得到的股票代码获取实时交易数据（您可以理解为日线的最新数据），该接口为券商数据源。
数据更新：实时
请求频率：1分钟300次 | 包年版1分钟3千次 | 白金版1分钟6千次
返回格式：标准Json格式      [{},...{}]
```json
{"pe":21.15,"ud":0.77,"pc":2.4093,"zf":6.1327,"tr":3.16,"pb_ratio":4.96,"p":32.73,"o":33.7,"h":33.98,"l":32.02,"yc":31.96,"cje":7609082900,"v":2314759,"pv":231475879,"tv":29395,"t":"2026-03-19 15:00:00"}
```
字段说明：
字段名称	数据类型	字段说明
p	number	最新价
o	number	开盘价
h	number	最高价
l	number	最低价
yc	number	前收盘价
cje	number	成交总额
v	number	成交总量
pv	number	原始成交总量
t	string	更新时间
ud	float	涨跌额
pc	float	涨跌幅
zf	float	振幅
t	string	更新时间
pe	number	市盈率
tr	number	换手率
pb_ratio	number	市净率
tv	number	成交量

## 沪深基金列表
API接口：https://api.biyingapi.com/fd/list/all/您的licence
接口说明：获取基础的基金代码和名称，用于后续接口的参数传入。
数据更新：每日16:20
请求频率：1分钟300次|包年版1分钟3千次|白金版1分钟6千次
返回格式：标准Json格式      [{},...{}]
数据范围样例：
```json
[{"dm":"159001.SZ","mc":"货币ETF易方达","jys":"SZ"},{"dm":"159003.SZ","mc":"招商快线ETF","jys":"SZ"}]
```
字段说明：
字段名称	数据类型	字段说明
dm	string	基金代码，如：159001.SZ
mc	string	基金名称，如：货币ETF
jys	string	交易所，"sh"表示上证，"sz"表示深证

## ETF基金列表
API接口：https://api.biyingapi.com/fd/list/etf/您的licence
接口说明：获取基础的基金代码和名称，用于后续接口的参数传入。
数据更新：每日16:20
请求频率：1分钟300次|包年版1分钟3千次|白金版1分钟6千次
返回格式：标准Json格式      [{},...{}]
数据范围样例：
```json
[{"dm":"159001.SZ","mc":"货币ETF易方达","jys":"SZ"},{"dm":"159003.SZ","mc":"招商快线ETF","jys":"SZ"}]
```
字段说明：
字段名称	数据类型	字段说明
dm	string	基金代码，如：159718.SZ
mc	string	基金名称，如：港股医药ETF
jys	string	交易所，"sh"表示上证，"sz"表示深证

## 基金实时数据
API接口：https://api.biyingapi.com/fd/real/time/基金代码(如159001)/您的licence
接口说明：根据《沪深基金列表》得到的基金代码获取实时交易数据（您可以理解为日线的最新数据），该接口为券商数据源。
数据更新：盘中实时
请求频率：1分钟300次|包年版1分钟3千次|白金版1分钟6千次
返回格式：标准Json格式      [{},...{}]
数据范围样例：
```json
{"pe":0,"ud":-0.269,"pc":-9.2313,"zf":5.2162,"p":2.645,"o":2.701,"h":2.777,"l":2.625,"yc":2.914,"cje":1065962800,"v":3948970,"pv":394897017,"tv":61710,"t":"2026-03-19 15:00:00"}

```
字段说明：
字段名称	数据类型	字段说明
p	number	最新价
o	number	开盘价
h	number	最高价
l	number	最低价
yc	number	前收盘价
cje	number	成交总额
v	number	成交总量
pv	number	原始成交总量
ud	float	涨跌额
pc	float	涨跌幅
zf	float	振幅
t	string	更新时间
pe	number	市盈率
tr	number	换手率
pb_ratio	number	市净率
tv	number	成交量