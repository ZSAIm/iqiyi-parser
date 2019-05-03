##############################################
#
# author: ZSAIm
#
# github: https://github.com/ZSAIm/PyJSCaller
#
##############################################

import subprocess
import traceback, os

HANDLER_NAME = '___'
NODEPATH = ''


class Sesson:
    def __init__(self, _file):
        self._methods = {
            '{}': Method(None, '{}'),
            '[]': Method(None, '[]'),
        }
        self.locals = MethodPool()
        self._exec_expr = []
        self._cells = []
        self._file = _file
        self.closed = False

        self._full_res = None

    def __enter__(self):
        return self

    def enter(self):
        return self.__enter__()

    def leave(self):
        self.run()
        self.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            traceback.print_exc()
        else:
            self.run()
            self.close()

    def require(self, *args):
        methods = []
        for i in args:
            if i in self._methods:
                methods.append(self._methods[i])
                continue

            method = Method(None, i)
            self._methods[i] = method
            methods.append(method)
            setattr(self.locals, i, method)

        return methods if len(methods) != 1 else methods[0]

    def run(self):
        if self._full_res:
            return

        for i in self._exec_expr:
            self.__extract_expr__(i)

        exec_code = self.getJSExecCode()

        with open('TMP.js', 'w') as f:
            with open(self._file, 'r') as origin:
                f.write(origin.read() + exec_code)

        res = pipe_eval('TMP.js')
        for i, j in enumerate(self._cells):
            j.set(res[i])

        for i in self._exec_expr:
            i.setRespond(self)

        self._full_res = res



    def addCell(self, handler):
        self._cells.append(handler)


    def getLocals(self):
        return self.locals

    def __extract_parent__(self, expr):
        if expr._parent:
            self.__extract_parent__(expr._parent)
        if expr.getResult() not in self._cells:
            self.addCell(expr.getResult())

    def __extract_result__(self, res):
        exprs = res.getExprs()

        for i in exprs:
            self.__extract_expr__(i)

        if res not in self._cells:
            self.addCell(res)

    def getCells(self):
        return self._cells

    def __extract_expr__(self, expr):
        if expr.isResult():
            self.__extract_result__(expr.getResult())
            self.__extract_parent__(expr)
        else:
            left = expr.getLeft()
            right = expr.getRight()
            if isinstance(left, Express):
                self.__extract_expr__(left)
            if isinstance(right, Express):
                self.__extract_expr__(right)

    def call(self, expr):
        if isinstance(expr, Express):
            if expr not in self._exec_expr:
                self._exec_expr.append(expr)
            return expr
        else:
            if isinstance(expr, dict):
                _kwarg_expr = {}
                for i, j in expr.items():
                    if isinstance(j, list) or isinstance(j, dict):
                        _kwarg_expr[i] = self.call(j)
                    else:
                        _kwarg_expr[i] = j

                res = Result(None, '{}', **_kwarg_expr)
            elif isinstance(expr, list) or isinstance(expr, tuple):
                _args_expr = []
                for i in expr:
                    if isinstance(i, list) or isinstance(i, dict):
                        _args_expr.append(self.call(i))
                    else:
                        _args_expr.append(i)

                res = Result(None, '[]', *_args_expr)
            else:
                res = None

            _expr = Express(None, None, res)
            self._exec_expr.append(_expr)
            return _expr

    def close(self):
        self.closed = True


    def getJSExecCode(self):
        """
            var HANDLER_NAME = [];

            HANDLER_NAME.push(...);
            ...

            console.log(JSON.stringify(HANDLER_NAME));

        """

        core_str = []
        for i in self._cells:
            value = i.getJSExpr(self)
            core_str.append('%s.push(%s);' % (HANDLER_NAME, value))

        template = ';\nvar %s=[];\n%s;\nconsole.log(JSON.stringify(%s))' % (
            HANDLER_NAME, str('\n'.join(core_str)), HANDLER_NAME)
        return template


class Express:
    def __init__(self, parent=None, operator=None, operands=None):
        self._parent = parent
        self.operator = operator
        self.operands = operands
        self.locals = MethodPool()
        self._methods = {}

    def getOperator(self):
        return self.operator

    def hasExpress(self):
        return self.operator is None and not self.getResult().hasExpress()

    def isBottom(self):
        return self.operator is None and not self.getResult().hasExpress()

    def isResult(self):
        return self.operator is None

    def getResult(self):
        if not self.isResult():
            raise ValueError()
        return self.operands

    def getLeft(self):
        return self.operands[0]

    def getRight(self):
        return self.operands[1]

    def getMethod(self, name):
        if name not in self._methods:
            raise Exception('method ( %s ) is not been required' % name)
        return self._methods[name]


    def getLocals(self):
        return self.locals

    def require(self, *args):
        methods = []
        for i in args:
            if i in self._methods:
                methods.append(self._methods[i])
                continue

            method = Method(self, i)
            self._methods[i] = method
            methods.append(method)
            setattr(self.locals, i, method)
            if not hasattr(self, i):
                setattr(self, i, method)

        return methods

    def setRespond(self, sess):
        if self.isResult():
            cells = sess.getCells()
            self.operands = cells[cells.index(self.getResult())]
        else:
            for i in self.operands:
                if isinstance(i, Express):
                    i.setRespond(sess)


    def getValue(self):
        if self.isResult():
            return self.getResult().get()
        else:
            eval_str = []
            for i in self.operands:
                if isinstance(i, Express):
                    eval_str.append(_expr_type_text_(i.getValue()))
                else:
                    eval_str.append(_expr_type_text_(i))
            try:
                res = eval(self.operator.join(eval_str))
            except Exception as e:

                raise ValueError('Express(%s): %s' % (self.operator.join(eval_str), str(e)))
            return res

    def getJSParent(self, sess):
        parent_str = []
        if self._parent:
            parent_str.append(self._parent.getJSParent(sess))
        else:
            return ''

    def __getParentText__(self):
        if self._parent:
            return self._parent.__getParentText__().extend(self.getResult().getExprText())
        else:
            return [self.getResult().getExprText()]

    def getParentText(self):
        return '.'.join(self.__getParentText__()[:-1])

    def getJSExpr(self, sess):

        if self.isResult():

            return '%s[%d]' % (HANDLER_NAME, sess.getCells().index(self.getResult()))
        else:
            jscode = []
            for i in self.operands:
                if isinstance(i, Express):
                    jscode.append(i.getJSExpr(sess))
                else:
                    code = _expr_type_text_(i)
                    jscode.append(code)
            # else:

            return self.operator.join(jscode)

    def __getExprText__(self):
        pass


    def getExprText(self):

        if self.isResult():
            code = self.getResult().getExprText()
            return code
        else:
            jscode = []
            for i in self.operands:
                if isinstance(i, Express):
                    jscode.append(i.getExprText())
                else:
                    code = _expr_type_text_(i)
                    jscode.append(code)
            return '%s' % self.operator.join(jscode)

    def __add__(self, other):
        return Express(None, '+', (self, other))

    def __radd__(self, other):
        return Express(None, '+', (other, self))

    def __sub__(self, other):
        return Express(None, '-', (self, other))

    def __rsub__(self, other):
        return Express(None, '-', (other, self))

    def __mul__(self, other):
        return Express(None, '*', (self, other))

    def __rmul__(self, other):
        return Express(None, '*', (other, self))

    def __div__(self, other):
        return Express(None, '/', (self, other))

    def __rdiv__(self, other):
        return Express(None, '*', (other, self))

    def __str__(self):
        return self.getExprText()


class MethodPool:
    def __init__(self):
        pass

    # def __getattr__(self, item):
    #     return object.__getattribute__(self, item)



class Method:
    def __init__(self, parent, name):
        self._parent = parent
        self.name = name

    def __call__(self, *args, **kwargs):
        return Express(self._parent, None, Result(self._parent, self.name, *args, **kwargs))


class Result:
    def __init__(self, parent, met_name, *args, **kwargs):
        self._parent = parent
        self.met_name = met_name
        self.args = []
        self.kwargs = {}
        self.res = None

        for i in args:
            if isinstance(i, list) or isinstance(i, tuple):
                self.args.append(Express(parent, None, Result(parent, '[]', *i)))
            elif isinstance(i, dict):
                self.args.append(Express(parent, None, Result(parent, '{}', **i)))
            else:
                self.args.append(i)

        for i, j in kwargs.items():
            if isinstance(j, list) or isinstance(j, tuple):
                self.kwargs[i] = Express(parent, None, Result(parent, '[]', *j))
            elif isinstance(j, dict):
                self.kwargs[i] = Express(parent, None, Result(parent, '{}', **j))
            else:
                self.kwargs[i] = j

    def getExprText(self):

        if self.met_name == '{}':
            _args_str = []
            for i, j in self.kwargs.items():
                data = _expr_type_text_(i), j.getExprText() if isinstance(j, Express) else _expr_type_text_(j)
                _args_str.append(data)

            _kwargs_str = ['%s: %s' % (i[0], i[1]) for i in _args_str]
            return '{%s}' % ', '.join(_kwargs_str)
        elif self.met_name == '[]':
            _args_str = []
            for i in self.args:
                if isinstance(i, Express):
                    _args_str.append(_expr_type_text_(i.getExprText()))
                else:
                    _args_str.append(_expr_type_text_(i))

            return '[%s]' % ', '.join([_expr_type_text_(i) for i in _args_str])

        else:
            parent_str = self._parent.getExprText() + '.' if self._parent else ''
            _args_str = []
            for i in self.args:
                if isinstance(i, Express):
                    _args_str.append(i.getExprText())
                else:
                    _args_str.append(_expr_type_text_(i))
            return '%s%s(%s)' % (parent_str, self.met_name, ','.join(_args_str))

    def __str__(self):
        return self.getExprText()

    def __eq__(self, other):
        return id(other) == id(self)
        # if other.met_name != self.met_name:
        #     return False
        #
        # if len(other.args) != len(self.args) or len(self.kwargs) != len(other.kwargs):
        #     return False
        #
        # for i in self.args:
        #     if i not in other.args:
        #         return False
        #
        # for i, j in self.kwargs.items():
        #     if i not in other.kwargs or other.kwargs[i] != j:
        #         return False
        #
        # return True


    def getArgs(self):
        return self.args

    def getKwargs(self):
        return self.kwargs

    def set(self, res):
        self.res = res

    def get(self):
        return self.res

    def getJSExpr(self, sess):
        if self.met_name == '{}':
            _args_str = []
            for i, j in self.kwargs.items():

                data = _expr_type_text_(i), j.getJSExpr(sess) if isinstance(j, Express) else _expr_type_text_(j)
                _args_str.append(data)

            _kwargs_str = ['%s: %s' % (i[0], i[1]) for i in _args_str]
            return '{%s}' % ', '.join(_kwargs_str)

        elif self.met_name == '[]':
            _args_str = []
            for i in self.args:
                _args_str.append(i.getJSExpr(sess) if isinstance(i, Express) else _expr_type_text_(i))

            return '[%s]' % ', '.join([str(i) for i in _args_str])


        else:
            parent_str = '%s[%d].' % (HANDLER_NAME, sess.getCells().index(self._parent.getResult())) if self._parent else ''
            _args_str = []
            for i in self.args:
                if isinstance(i, Express):
                    _args_str.append(i.getJSExpr(sess))
                else:
                    _args_str.append(_expr_type_text_(i))
            return '%s%s(%s)' % (parent_str, self.met_name, ','.join(tuple(_args_str)))


    def getExprs(self):
        exprs = []
        for i in self.args:
            if isinstance(i, Express):
                exprs.append(i)

        for i in self.kwargs.values():
            if isinstance(i, Express):
                exprs.append(i)

        return exprs



def _expr_type_text_(expr):
    return str([expr])[1:-1]

def pipe_eval(jsfile):
    global NODEPATH
    js_ctx = [os.path.join(NODEPATH, 'node'), jsfile]

    res = subprocess.check_output(js_ctx, shell=True, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    return eval(res)

def setNodePath(path):
    global NODEPATH
    NODEPATH = path



if __name__ == "__main__":
    setNodePath('')

    import time
    start = time.clock()

    a = 2
    b = 3
    c = 5

    with Sesson('example.js') as sess:
        triAdd, triMul = sess.require('triAdd', 'triMul')
        res = triMul(triAdd(a, b, c), triAdd(c, b, a), 1)
        sess.call(res)

    print(res.getValue())
    print('total time：%s' % (time.clock() - start))

    start = time.clock()

    with Sesson('example.js') as sess:
        require = sess.require('require')

        querystring = require('querystring')
        querystring.require('stringify')

        query_dict = {'one': 2, 'two': [1, 'haha', {'h': res.getValue(), 'ss': {'2': 2}}]}

        query_str = querystring.stringify(query_dict)

        sess.call(query_str)

    print(query_str.getValue())
    print('total time: %s' % (time.clock() - start))


