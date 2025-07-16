document.addEventListener("DOMContentLoaded", function () {
    const toggleBtn = document.getElementById("sidebarToggle");
    const sidebar = document.querySelector(".side_menu");

    // 侧边栏选中
    const currentPath = window.location.pathname;
    const sideMenuItems = document.querySelectorAll(".side_menu_option");
    let matched = false;

    sideMenuItems.forEach(item => {
        const href = item.getAttribute("href");
        if (href && currentPath === href) {
            item.classList.add("active");
            matched = true;
        }
        item.addEventListener("click", function () {
            sideMenuItems.forEach(i => i.classList.remove("active"));
            this.classList.add("active");
        });
    });
    if (!matched && sideMenuItems.length > 0) {
        sideMenuItems[0].classList.add("active");
    }

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", function () {
            sidebar.classList.toggle("collapsed"); // PC 模式用
            sidebar.classList.toggle("show");      // 移动模式用
        });
    }

    function updateTodoCounts(range = "today") {
        const todos = document.querySelectorAll(".todo_item");
        const today = new Date();
        let completed = 0;
        let inProgress = 0;
        let overdue = 0;

        todos.forEach(todo => {
            const status = parseInt(todo.dataset.status);
            const deadlineStr = todo.dataset.deadline;
            const deadline = new Date(deadlineStr);

            if (isInRange(deadline, range, today)) {
                if (status === 2) completed++;
                if (status === 1) inProgress++;
            }
            if ((status === 0 || status === 1) && deadline < today) overdue++;
        });

        document.getElementById("todo_done_count").textContent = completed;
        document.getElementById("todo_doing_count").textContent = inProgress;
        document.getElementById("todo_overdue_count").textContent = overdue;

        // 可选新增总数统计
        const total = completed + inProgress;
        const totalCountEl = document.getElementById("todo_total_count");
        if (totalCountEl) totalCountEl.textContent = total;
    }

    function isInRange(date, range, today) {
        switch (range) {
            case "today":
                return isSameDay(date, today);
            case "yesterday":
                const yest = new Date(today);
                yest.setDate(today.getDate() - 1);
                return isSameDay(date, yest);
            case "this_week":
                return isSameWeek(date, today);
            case "this_month":
                return date.getMonth() === today.getMonth() &&
                       date.getFullYear() === today.getFullYear();
            case "this_year":
                return date.getFullYear() === today.getFullYear();
            case "all":
                return true;
            default:
                return false;
        }
    }

    function isSameDay(d1, d2) {
        return d1.getFullYear() === d2.getFullYear() &&
               d1.getMonth() === d2.getMonth() &&
               d1.getDate() === d2.getDate();
    }

    function isSameWeek(date, today) {
        const day = today.getDay(); // Sunday=0
        const startOfWeek = new Date(today);
        startOfWeek.setDate(today.getDate() - day);
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6);

        return date >= startOfWeek && date <= endOfWeek;
    }

    // 分享按钮复制链接和用户信息
    const shareBtn = document.getElementById("share");
    if (shareBtn) {
        shareBtn.addEventListener("click", function () {
            // 获取当前链接
            const url = window.location.href;
            // 获取用户id
            let userId = "";
            const userIdSpan = document.getElementById("user_id");
            if (userIdSpan) {
                // 假设内容是 "id: 123"
                const match = userIdSpan.textContent.match(/id: (\d+)/);
                if (match) userId = match[1];
            }
            // 获取用户名
            let userName = "";
            const userNameSpan = document.getElementById("user_name");
            if (userNameSpan) {
                userName = userNameSpan.textContent.trim();
            }
            // 拼接内容
            const text = `Link: ${url}\nUser: ${userName}\nUser ID: ${userId}`;
            // 兼容性复制到剪切板
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(function () {
                    showCopyTip("Copied to clipboard!");
                }, function () {
                    alert("Replication failed, copy it manually!");
                });
            } else {
                // 兼容旧浏览器
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                try {
                    document.execCommand('copy');
                    showCopyTip("Copied to clipboard!");
                } catch (err) {
                    alert("Replication failed, copy it manually!");
                }
                document.body.removeChild(textarea);
            }
        });
    }

    // 顶部提示条
    function showCopyTip(msg) {
        let tip = document.getElementById('spirit-copy-tip');
        if (!tip) {
            tip = document.createElement('div');
            tip.id = 'spirit-copy-tip';
            tip.style.position = 'fixed';
            tip.style.top = '0';
            tip.style.left = '0';
            tip.style.width = '100%';
            tip.style.zIndex = '9999';
            tip.style.background = '#23272f';
            tip.style.color = '#fff';
            tip.style.textAlign = 'center';
            tip.style.fontSize = '1.1rem';
            tip.style.padding = '12px 0';
            tip.style.boxShadow = '0 2px 8px #047e9b55';
            document.body.appendChild(tip);
        }
        tip.textContent = 'Spirit Todo tips: ' + msg;
        tip.style.display = 'block';
        clearTimeout(tip._timer);
        tip._timer = setTimeout(() => { tip.style.display = 'none'; }, 2000);
    }

    // 用户信息弹出框逻辑
    const userInfoBtn = document.getElementById("user-info-btn");
    const userInfoPopover = document.getElementById("user-info-popover");
    if (userInfoBtn && userInfoPopover) {
        userInfoBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            // 获取用户信息
            const userIdSpan = document.getElementById("user_id");
            const userNameSpan = document.getElementById("user_name");
            let userId = userIdSpan ? userIdSpan.textContent.replace(/id: ?/, '') : '';
            let userName = userNameSpan ? userNameSpan.textContent.trim() : '';
            // 获取 join_time（可放在 userNameSpan 的 data-join-time 属性，或后续补充）
            let joinTime = userNameSpan ? userNameSpan.getAttribute('data-join-time') : '';
            // 填充内容
            userInfoPopover.querySelector('.popover-body').innerHTML = `
                <b>User Info</b><br>
                Username: ${userName || 'N/A'}<br>
                User ID: ${userId || 'N/A'}<br>
                Join Time: ${joinTime || 'N/A'}
            `;
            // 定位弹出框，防止超出右侧
            const rect = userInfoBtn.getBoundingClientRect();
            const popoverWidth = userInfoPopover.offsetWidth || 220;
            let left = window.scrollX + rect.left;
            const rightEdge = left + popoverWidth;
            const maxRight = window.scrollX + window.innerWidth - 12;
            if (rightEdge > maxRight) {
                left = maxRight - popoverWidth;
                if (left < 0) left = 0;
            }
            userInfoPopover.style.top = (window.scrollY + rect.bottom + 8) + 'px';
            userInfoPopover.style.left = left + 'px';
            userInfoPopover.style.display = 'block';
            // 动态设置箭头位置
            const arrow = userInfoPopover.querySelector('.popover-arrow');
            if (arrow) {
                // SVG中心点相对于弹窗左侧的距离
                const svgCenter = rect.left + rect.width / 2;
                const popoverLeft = left;
                const arrowLeft = svgCenter - popoverLeft - 8; // 8为箭头宽度一半
                arrow.style.left = Math.max(arrowLeft, 12) + 'px'; // 最小12px，防止溢出
            }
        });
        // 点击其他地方关闭弹出框
        document.addEventListener("click", function () {
            userInfoPopover.style.display = 'none';
        });
        // 阻止弹出框内部点击冒泡
        userInfoPopover.addEventListener("click", function (e) {
            e.stopPropagation();
        });
    }

    // 登出按钮逻辑
    const logoutButton = document.querySelector('a.side_menu_end');
    if (logoutButton) {
        logoutButton.addEventListener('click', function(e) {
            e.preventDefault(); // 阻止默认的链接跳转行为
            window.location.href = this.href; // 直接跳转到后端登出路由
        });
    }

    // ====== 全局功能定位搜索 ======
    const functionMap = {
        "Heat Map": "/static/echarts/heat_map.html",
        "Bar Chart": "/static/echarts/bar_chart.html",
        "Line Chart": "/static/echarts/line_chart.html",
        "Pie Chart": "/static/echarts/pie_radius.html",
        "Trash": "/Spirit/TodoPage/Todo#trash", // 跳转到todo页面并定位回收站tab
        "Recycle Bin": "/Spirit/TodoPage/Todo#trash",
        "Homepage": "/Spirit/Homepage",
        "Home": "/Spirit/Homepage"
        // 你可以继续扩展
    };

    const searchInput = document.getElementById("search1");
    if (searchInput) {
        // 回车搜索
        searchInput.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                handleFunctionSearch();
            }
        });
        // 点击搜索图标也能跳转
        const searchIcon = searchInput.parentElement.querySelector(".search-icon");
        if (searchIcon) {
            searchIcon.style.cursor = "pointer";
            searchIcon.addEventListener("click", handleFunctionSearch);
        }
    }

    function handleFunctionSearch() {
        const query = searchInput.value.trim();
        if (!query) return;
        // 忽略大小写匹配
        const matchedKey = Object.keys(functionMap).find(
            key => key.toLowerCase() === query.toLowerCase()
        );
        if (matchedKey) {
            window.location.href = functionMap[matchedKey];
        } else {
            alert("未找到对应功能页面！");
        }
    }
});
// 新建/编辑项目或Todo表单校验时间顺序（外部脚本迁移版）
document.addEventListener("DOMContentLoaded", function () {
    let form = document.getElementById("newProjectForm");
    if (!form) {
        let forms = document.getElementsByTagName("form");
        for (let i = 0; i < forms.length; i++) {
            if (forms[i].action && forms[i].action.indexOf('new_project') !== -1) {
                form = forms[i];
                break;
            }
        }
    }
    if (form) {
        console.log("✅ Inline JS 校验逻辑运行了！");
        form.addEventListener("submit", function (e) {
            // ======= 表单校验（原有内容） =======
            const startInput = document.getElementById("start_time") || document.getElementById("new_project_start");
            const deadlineInput = document.getElementById("new_project_ddl") || document.getElementById("deadline");
            const completedInput = document.getElementById("completed_time") || document.getElementById("new_project_completed");

            const title = document.getElementById("new_project_title");
            const brief = document.getElementById("new_project_brief");
            const content = document.getElementById("new_project_content");

            if (!title || !brief || !content || !title.value.trim() || !brief.value.trim() || !content.value.trim()) {
                alert("Please complete all required fields: title, brief, and content.");
                e.preventDefault();
                return;
            }

            console.log("🐛 base.js loaded!");
            console.log("【DEADLINE_INPUT VALUE】", deadlineInput && deadlineInput.value);

            if (!deadlineInput) {
                alert("Deadline input not found!");
                e.preventDefault();
                return;
            }

            if (!deadlineInput.value.trim()) {
                alert("Please set a deadline (JS强提醒)!");
                e.preventDefault();
                return;
            }

            if (!startInput) return;

            const startTime = new Date(startInput.value);

            if (deadlineInput && deadlineInput.value) {
                const deadline = new Date(deadlineInput.value);
                if (startTime > deadline) {
                    alert("Start time must be earlier than deadline.");
                    e.preventDefault();
                    return;
                }
            }

            if (completedInput && completedInput.value) {
                const completed = new Date(completedInput.value);
                if (startTime > completed) {
                    alert("Start time must be earlier than completed time.");
                    e.preventDefault();
                    return;
                }
            }

            // ======= fetch 提交（新增部分） =======
            e.preventDefault();

            // WTForms日期时间格式兼容
            const formatDatetime = val => val ? val.replace('T', ' ') : "";

            // 收集所有字段
            const data = {
                title: title.value.trim(),
                brief: brief.value.trim(),
                content: content.value.trim(),
                deadline: formatDatetime(deadlineInput.value),
                start_time: formatDatetime(startInput.value),
                completed_time: completedInput ? formatDatetime(completedInput.value) : "",
                mail_notify: document.getElementById("new_project_option1")?.checked || false,
                important: document.querySelector("input[name='important']")?.checked || false
            };

            console.log("DEBUG SUBMIT DATA", data);

            // 提交按钮禁用，防止重复提交
            const submitBtn = form.querySelector("button[type='submit']");
            if (submitBtn) submitBtn.disabled = true;

            fetch(form.action, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                console.log(result);
                if (result.success) {
                    alert("Project created successfully!");
                    window.location.reload();
                } else {
                    alert(result.error || "Create failed!");
                }
            })
            .catch(err => {
                alert("Request error!");
            })
            .finally(() => {
                if (submitBtn) submitBtn.disabled = false;
            });
        });
    }
});