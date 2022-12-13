var prevScrollpos = window.pageYOffset;
window.onload = function()
{
document.getElementById("navbar").style.display = "none";
}
window.onscroll = function() {
  var currentScrollPos = window.pageYOffset;

  // 20 is an arbitrary number here, just to make you think if you need the prevScrollpos variable:
  if (currentScrollPos > 1250) {
    // I am using 'display' instead of 'top':
    document.getElementById("navbar").style.display = "initial";
  }
  else {
    document.getElementById("navbar").style.display = "none";
  }
}

