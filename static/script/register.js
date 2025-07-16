function bindEmailCaptchaClick() {
    $("#send_captcha").click(function (event) {
        var $this = $(this);
        event.preventDefault();

        var email = $("#email_enter").val();
        $.ajax({
            url: "/spirit/captcha/email?email=" + email,
            method: "GET",
            success: function (result) {
                var code = result['code'];
                if (code == 200) {
                    var countdown = 60;
                    // 开始倒计时之前，就取消按钮的点击事件
                    $this.off("click");
                    var timer = setInterval(function () {
                        $this.text(countdown);
                        countdown -= 1;
                        // 倒计时结束的时候执行
                        if (countdown <= 0) {
                            // 清掉定时器
                            clearInterval(timer);
                            // 将按钮的文字重新修改回来
                            $this.text("Send");
                            // 重新绑定点击事件
                            bindEmailCaptchaClick();
                        }
                    }, 1000);
                    // alert("邮箱验证码发送成功！");
                } else {
                    alert(result['message']);
                }
            },
            fail: function (error) {
                console.log(error);
            }
        })
    });
}

$(function () {
    bindEmailCaptchaClick();
})