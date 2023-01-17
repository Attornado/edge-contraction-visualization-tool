let $scrollUpBtn = $("#scrollUpBtn");

$(window).on("scroll", ev => {
    if($(window).scrollTop() >= $(window).height()/7)
        $scrollUpBtn.addClass("toShow");
    else
        $scrollUpBtn.removeClass("toShow");
});
$scrollUpBtn.on("click", ev => {
    $('html, body').animate({scrollTop:0}, '300');
    //equivalente a $(window).scrollTop(0), ma con animazione, ci spostiamo sulla parte superiore della pagina
});