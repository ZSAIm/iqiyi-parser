
$(function(){
	// 窗口修改事件
	$(window).resize(autoResize);
	// 折叠侧边栏
	$('#fold').click(toggleFoldSidebar);
	// 链接栏链接实时分析
	$('#urls').keyup(function(){

	});
	// 建立解析下载请求
	$('#go-download').click(function(){
		// 分割链接请求。
		var urls = $('#urls').val().split('\n').filter(function(str){
			return str && str.trim() && is_valid_uri(str);
		});
		// 创建新的任务
		// 目前只支持一个链接一个任务
		for(var i=0; i < urls.length; i++){
			TaskManager.create(urls[i]);
		}

	});

	autoResize();



});

// 字符串格式化
String.prototype.format = function(args) {
	var result = this;
	if (arguments.length > 0) {
		if (arguments.length == 1 && typeof (args) == "object") {
			for (var key in args) {
				if(args[key]!=undefined){
					var reg = new RegExp("({" + key + "})", "g");
					result = result.replace(reg, args[key]);
				}
			}
		}
		else {
			for (var i = 0; i < arguments.length; i++) {
				if (arguments[i] != undefined) {
					var reg = new RegExp("({[" + i + "]})", "g");
					result = result.replace(reg, arguments[i]);
				}
			}
		}
	}
	return result;
}
function autoResize(){
	// 组件栏自适应。
	var window_height = $(window).height();
	var window_width = $(window).width();
	var header_height = $('.navbar-static-top').height();
	var footer_height = $('.main-footer').height();
	var sidebar_width = $('.main-sidebar').width();
	// 侧边栏自动高度
	$('.main-sidebar').height(window_height - header_height);
	// 内容栏自动高度宽度。
	$('.main-content').height(window_height - header_height - footer_height);
}
function guid(){
	// 生成GUID作为任务ID
	function s4(){return (((1+Math.random())*0x10000)|0).toString(16).substring(1);}
	return s4()+s4()+s4();
}
function toggleFoldSidebar(){
	if($(this).hasClass('on')){
		$('.main-header .logo').animate({width: '180px'}, 'fast');
		$('.main-sidebar').animate({width: '180px'}, 'fast');
		$('.main-header .navbar').animate({marginLeft: '180px'}, 'fast');
		$('.main-footer').animate({marginLeft: '180px'}, 'fast');
		$('.main-content').animate({paddingLeft: '180px'}, 'fast');
		$(this).removeClass('on');
	}else{
		$('.main-header .logo').animate({width: '50px'}, 'fast');
		$('.main-sidebar').animate({width: '50px'}, 'fast');
		$('.main-header .navbar').animate({marginLeft: '50px'}, 'fast');
		$('.main-footer').animate({marginLeft: '50px'}, 'fast');
		$('.main-content').animate({paddingLeft: '50px'}, 'fast');
		$(this).addClass('on');
	}
}

function is_valid_uri(uri){
	// 返回是否为正确的URI链接。
	return true;
}


function Task(id, urls){
	// 任务组对象
	this.id = id;
	this.is_ready = false;
	this.is_finished = false;
	this.is_error = false;
	this.urls = urls.concat();
	// 任务所在节点
	this.note = $('#' + id);
}
Task.prototype = {
	get_ready: function(){
		// 任务准备就绪
		this.is_ready = true;
	},
	get_finished: function(){
		// 任务完成。
		this.is_finished = true;
	},
	get_error: function(){
		// 任务出错
		this.is_error = true;
	},
	update: function(){
		// 更新任务信息

	},
	update_detail: function(){
		//
	},

}

$(function(){
	// 任务管理器
	TaskManager = {
		all: {},
		unready: new Array(),
		running: new Array(),
		finished: new Array(),
		error: new Array(),
		item_model: '<div class="task" id="{id}"><div class="body-info col-xs-6"><div class="task-icon"><img src="{icon}"></img></div><div class="name-url"><span class="task-name">{name}}</span><span class="task-url">{url}</span></div></div><div class="realtime-info col-xs-4"><div class="progress"><div class="progress-bar"></div></div><div class="speed-time"><span class="task-speed">{speed}</span><span class="task-timeleft">{time_left}</span></div></div><div class="detail"><a class=" task-detail fa fa-angle-right"></a></div></div>',
		tasks_note: $('.main-content .tasks'),

		create: function(urls){
			// 使用列表来封装链接
			if(!Array.isArray(urls))
				urls = [urls];
			// 创建新的任务
			var tid = 't_' + guid();
			this.unready.push(tid);
			// 添加任务项进入任务列表节点
			this.tasks_note.append(this.item_model.format({
				id: tid,
				name: tid,
				url: urls.join('\n'),
				speed: '0 KB/S',
				time_left: '00'
			}));
			this.all[tid] = new Task(tid, urls);

			// 发送添加任务请求。
			var data = {
				urls: urls,
				options: {
					dir: $('#options #dir').val(),
					overwrite: $('#options #overwrite').val(),
					max_speed: $('#options #max_speed').val(),
				},
			};
			// POST提交添加解析下载请求。
			$.post('godownload', JSON.stringify(data), function(data){
				if(data.code == 1){
					// 解析成功
					alert('任务建立成功。');
				}
			}, 'json').fail(function(xhr, statusText, dataText){
				alert(statusText + ':' + dataText);
			});


			return tid;
		},

		refresh: function(){
			// 刷新任务信息
		},


	}
});

