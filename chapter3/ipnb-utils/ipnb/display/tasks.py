from IPython.display import display
from IPython.kernel.zmq.serialize import unpack_apply_message
from IPython.parallel.client.asyncresult import AsyncResult, AsyncMapResult

def display_task(client, ar):
    def get_msg_ids(x):
        if isinstance(x, basestring):
            return [x]
        elif hasattr(x, "msg_ids"):
            return x.msg_ids
        elif isinstance(x, list):
            return [item for sublist in [get_msg_ids(e) for e in x] for item in sublist]
        else:
            return []

    time_keys = ["submitted", "started", "completed", "received"]
    keys = ["stdout", "stderr"]
    meta_keys = ["queue", "header", "result_header", "content", "result_content", "metadata", "result_metadata"]

    for i, msg_id in enumerate(get_msg_ids(ar)):
        tasks = client.db_query({'msg_id' : msg_id }, keys=["buffers"] + time_keys + keys)
        try:
            t = tasks[0]
        except:
            print("task {} not found".format(msg_id))
            continue

        # title
        try:
            f, args, kwargs = unpack_apply_message(t['buffers'])
            if len(args) > 0 and isinstance(args[0], partial):
                fname = fn.func.__name__
                args = args[1:] if len(args) > 1 else []
                #args = fn.args + args[1:] if len(args) > 1 else []
                #kwargs.update(fn.keywords)
            else:
                fname = f.__name__
            name = [fname, "("]
            name += [", ".join([str(v) for v in args] + ["{}={}".format(k, v) for k, v in kwargs.items()])]
            name += [") [", t["msg_id"], "]"]
            if i != 0:
                print("")
        except:
            name = "[{}]".format(msg_id)

        if i > 0:
            print()

        print("[{}] {}".format(i, "".join(name)))

        # status
        sb = []
        time_labels = ["Submitted", "Started", "Completed", "Received"]
        last_date = None
        for label, key in zip(time_labels, time_keys):
            if key not in t or t[key] is None:
                continue
            date = t[key].strftime("%Y-%m-%d")
            time = t[key].strftime("%H:%M:%S")
            date_time = date + " " + time if date != last_date else time
            sb += ["{}: {}".format(label, date_time)]
            last_date = date
        if len(sb) > 0:
            print("\n" + ", ".join(sb))

        # keys
        for k in keys:
            if k not in t or t[k] is None:
                continue
            v = t[k]
            if isinstance(v, basestring) and len(v) == 0:
                continue
            print("\n[{}]".format(k))
            print(t[k])

        # result
        if isinstance(ar, AsyncResult) and ar.ready():
            r = ar.r[i] if isinstance(ar, AsyncMapResult) else ar.r
            if r is not None:
                print("[return]")
                display(r)

def display_tasks(client, groupby=None):
	"""
	Show client running tasks.
	:param groupby: Group by node hostname instead of engine.
	"""
	pass