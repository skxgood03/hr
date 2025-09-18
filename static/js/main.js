// 人事工资管理系统 - 主要JavaScript文件

$(document).ready(function() {
    // 初始化工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 初始化弹出框
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // 自动隐藏警告消息
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // 确认删除对话框
    $('.delete-confirm').on('click', function(e) {
        e.preventDefault();
        var url = $(this).attr('href');
        var itemName = $(this).data('item-name') || '该项目';
        
        if (confirm('确定要删除 "' + itemName + '" 吗？此操作不可撤销。')) {
            window.location.href = url;
        }
    });

    // 表格行点击事件
    $('.table-row-clickable').on('click', function() {
        var url = $(this).data('url');
        if (url) {
            window.location.href = url;
        }
    });

    // 搜索框实时搜索
    let searchTimeout;
    $('.search-input').on('input', function() {
        clearTimeout(searchTimeout);
        var query = $(this).val();
        var form = $(this).closest('form');
        
        searchTimeout = setTimeout(function() {
            if (query.length >= 2 || query.length === 0) {
                form.submit();
            }
        }, 500);
    });

    // 表单验证
    $('.needs-validation').on('submit', function(e) {
        if (!this.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });

    // 数字输入框验证
    $('.number-input').on('input', function() {
        var value = $(this).val();
        if (value && isNaN(value)) {
            $(this).val(value.replace(/[^0-9.]/g, ''));
        }
    });

    // 电话号码格式化
    $('.phone-input').on('input', function() {
        var value = $(this).val().replace(/\D/g, '');
        if (value.length >= 11) {
            value = value.substring(0, 11);
        }
        $(this).val(value);
    });

    // 邮箱验证
    $('.email-input').on('blur', function() {
        var email = $(this).val();
        var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (email && !emailRegex.test(email)) {
            $(this).addClass('is-invalid');
            if (!$(this).siblings('.invalid-feedback').length) {
                $(this).after('<div class="invalid-feedback">请输入有效的邮箱地址</div>');
            }
        } else {
            $(this).removeClass('is-invalid');
            $(this).siblings('.invalid-feedback').remove();
        }
    });

    // 批量操作
    $('#selectAll').on('change', function() {
        $('.item-checkbox').prop('checked', $(this).prop('checked'));
        updateBatchActions();
    });

    $('.item-checkbox').on('change', function() {
        updateBatchActions();
        
        // 更新全选状态
        var totalCheckboxes = $('.item-checkbox').length;
        var checkedCheckboxes = $('.item-checkbox:checked').length;
        
        if (checkedCheckboxes === 0) {
            $('#selectAll').prop('indeterminate', false).prop('checked', false);
        } else if (checkedCheckboxes === totalCheckboxes) {
            $('#selectAll').prop('indeterminate', false).prop('checked', true);
        } else {
            $('#selectAll').prop('indeterminate', true);
        }
    });

    function updateBatchActions() {
        var checkedCount = $('.item-checkbox:checked').length;
        if (checkedCount > 0) {
            $('.batch-actions').show();
            $('.batch-count').text(checkedCount);
        } else {
            $('.batch-actions').hide();
        }
    }

    // 批量删除
    $('.batch-delete').on('click', function() {
        var checkedItems = $('.item-checkbox:checked');
        if (checkedItems.length === 0) {
            alert('请选择要删除的项目');
            return;
        }
        
        if (confirm('确定要删除选中的 ' + checkedItems.length + ' 个项目吗？此操作不可撤销。')) {
            var ids = [];
            checkedItems.each(function() {
                ids.push($(this).val());
            });
            
            // 创建表单提交
            var form = $('<form method="post" action="' + $(this).data('url') + '">');
            form.append('<input type="hidden" name="csrfmiddlewaretoken" value="' + $('[name=csrfmiddlewaretoken]').val() + '">');
            form.append('<input type="hidden" name="ids" value="' + ids.join(',') + '">');
            $('body').append(form);
            form.submit();
        }
    });

    // 导出功能
    $('.export-btn').on('click', function() {
        var format = $(this).data('format');
        var url = $(this).data('url');
        
        // 显示加载状态
        var originalText = $(this).html();
        $(this).html('<span class="loading"></span> 导出中...');
        $(this).prop('disabled', true);
        
        // 创建隐藏的iframe来下载文件
        var iframe = $('<iframe style="display:none;"></iframe>');
        iframe.attr('src', url + '?format=' + format);
        $('body').append(iframe);
        
        // 恢复按钮状态
        setTimeout(function() {
            $('.export-btn').html(originalText).prop('disabled', false);
            iframe.remove();
        }, 3000);
    });

    // 图片预览
    $('.image-input').on('change', function() {
        var file = this.files[0];
        var preview = $(this).siblings('.image-preview');
        
        if (file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                preview.attr('src', e.target.result).show();
            };
            reader.readAsDataURL(file);
        } else {
            preview.hide();
        }
    });

    // 动态添加表单行
    $('.add-form-row').on('click', function() {
        var template = $(this).data('template');
        var container = $(this).data('container');
        var newRow = $(template).clone();
        
        // 更新表单字段名称
        var index = $(container + ' .form-row').length;
        newRow.find('input, select, textarea').each(function() {
            var name = $(this).attr('name');
            if (name) {
                $(this).attr('name', name.replace('__prefix__', index));
            }
        });
        
        $(container).append(newRow);
    });

    // 删除表单行
    $(document).on('click', '.remove-form-row', function() {
        $(this).closest('.form-row').remove();
    });

    // 页面加载完成后的处理
    $(window).on('load', function() {
        // 隐藏加载指示器
        $('.page-loading').fadeOut();
        
        // 显示页面内容
        $('.page-content').fadeIn();
    });

    // 返回顶部按钮
    $(window).scroll(function() {
        if ($(this).scrollTop() > 100) {
            $('.back-to-top').fadeIn();
        } else {
            $('.back-to-top').fadeOut();
        }
    });

    $('.back-to-top').on('click', function() {
        $('html, body').animate({scrollTop: 0}, 800);
        return false;
    });
});

// 工具函数
function showMessage(message, type = 'info') {
    var alertClass = 'alert-' + type;
    var alert = $('<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
                  message +
                  '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                  '</div>');
    
    $('.container-fluid').first().prepend(alert);
    
    setTimeout(function() {
        alert.fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function formatDate(dateString) {
    var date = new Date(dateString);
    return date.getFullYear() + '-' + 
           String(date.getMonth() + 1).padStart(2, '0') + '-' + 
           String(date.getDate()).padStart(2, '0');
}

function formatDateTime(dateString) {
    var date = new Date(dateString);
    return formatDate(dateString) + ' ' + 
           String(date.getHours()).padStart(2, '0') + ':' + 
           String(date.getMinutes()).padStart(2, '0');
}

// AJAX请求封装
function ajaxRequest(url, method = 'GET', data = null, successCallback = null, errorCallback = null) {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", $('[name=csrfmiddlewaretoken]').val());
            }
        }
    });
    
    $.ajax({
        url: url,
        method: method,
        data: data,
        dataType: 'json',
        success: function(response) {
            if (successCallback) {
                successCallback(response);
            }
        },
        error: function(xhr, status, error) {
            if (errorCallback) {
                errorCallback(xhr, status, error);
            } else {
                showMessage('请求失败: ' + error, 'danger');
            }
        }
    });
}