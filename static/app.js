//Fuctions run after document is ready
$(document).ready(function() {
    // Real-time username checking without reloading page
    $("#username").on("input", function(e) {
        $('#username_check').hide();
        if ($('#username').val() == null || $('#username').val() == "") {
            $('#username_check').show();
            $("#username_check").html("Username is required field.").css("color", "red");
        } else {
            $.ajax({
                type: "POST",
                url: "/user_check",
                data: {
                    username_input: $('#username').val()
                },
            }).done(function(data) {
                if (data == "Username available") {
                    $('#username_check').show();
                    $("#username_check").html(data).css("color", "green");
                } else {
                    $('#username_check').show();
                    $("#username_check").html(data).css("color", "red"); 
                }
            })
        }
    })

    // Real-time password strength check without reloading page
    let strength = {
        0: "Worst",
        1: "Bad",
        2: "Weak",
        3: "Good",
        4: "Strong"
    }
    
    let password = document.getElementById('password');
    let meter = document.getElementById('password_str_meter');
    let text = document.getElementById('password_str_text');

    password.addEventListener('input', function() {
    let val = password.value;

        // Update the text indicator
        if (val !== "") {
            let val_length = val.length;
            if (val_length < 6) {
                $("#password_str_text").html("Password is too short").css("color", "red"); 
            } else {
                let result = zxcvbn(val);

                // Update the password strength meter
                meter.value = result.score;
                
                if (result.score < 2){
                    $("#password_str_text").html("Strength: " + strength[result.score]).css("color", "red");    
                }
                if (result.score == 2) {
                    $("#password_str_text").html("Strength: " + strength[result.score]).css("color", "orange");
                }
                if (result.score > 2) {
                    $("#password_str_text").html("Strength: " + strength[result.score]).css("color", "green");
                }
            }  
        } else {
            $("#password_str_text").html("Password is required field").css("color", "red");
        }
    })

    // Real-time checking if password fields match or not
    $("#confirmation").on("input", function(e) {
        if ($('#confirmation').val() == null || $('#confirmation').val() == "") {
            $('#password_match').show();
            $("#password_match").html("Must enter password again").css("color", "red");
        }
        if ($("#confirmation").val() == $("#password").val()) {
            $('#password_match').show();
            $("#password_match").html("Passwords match").css("color", "green");
        } else {
            $("#password_match").html("Passwords do NOT match").css("color", "red");
        }
    })
});