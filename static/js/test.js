var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
} 

  function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
      tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
      tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
  }

  document.getElementById("defaultOpen").click();



$(".header").click(function () {

  $header = $(this);
  //getting the next element
  $content = $header.next();
  //open up the content needed - toggle the slide- if visible, slide up, if not slidedown.
  $content.slideToggle(500, function () {
      //execute this after slideToggle is done
      //change text of header based on visibility of content div
      $header.text(function () {
          //change text based on condition
          return $content.is(":visible") ? "Collapse" : "Expand";
      });
  });

});



function collapse(element) {
    var ccontent = element.parentNode;
    var content = ccontent.parentNode;
    var tur = content.nextElementSibling;
    /*
    var dir = element.firstElementChild;
    
    triangle = dir.firstElementChild;
    */

    if (tur.style.display == "block") {
      tur.style.visibility = "hidden";
      tur.style.display = "none";
      element.style.transform = "rotate(90deg)";
    } else {
      tur.style.display = "block";
      tur.style.visibility = "visible";
      element.style.transform = "rotate(0deg)";
    }
    
    /*
    if (content.style.opacity == "1") {
      //content.style.visibility = "hidden";
      content.style.transition = "0.5s linear"
      content.style.opacity = "0";
      //content.style.display = "none";
      triangle.style.transform = "rotate(90deg)";
    } else {
      //content.style.visibility = "visible";
      content.style.transition = "0.5s linear"
      content.style.opacity = "1";
      triangle.style.transform = "rotate(0deg)";
      //content.style.display = "block";
    }
    */
}