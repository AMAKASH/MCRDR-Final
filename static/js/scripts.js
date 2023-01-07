let page = window.location.pathname;

//console.log("Log from global js");

if (page != "/") {
  let home_nav = document.getElementById("nav-home");
  let test_nav = document.getElementById("nav-testing");
  let dataset_nav = document.getElementById("nav-dataset");
  let rule_nav = document.getElementById("nav-rules");
  let corner_nav = document.getElementById("nav-cornerstones");
  home_nav.classList.remove("active");
  home_nav.removeAttribute("aria-current");

  if (page == "/rules") {
    rule_nav.classList.add("active");
  } else if (page == "/dataset") {
    dataset_nav.classList.add("active");
  } else if (page == "/dataset/testing") {
    test_nav.classList.add("active");
  } else {
    corner_nav.classList.add("active");
  }
}

//Upadte Footer Year Dynamically
const year_elm = document.getElementById("footer-year");
const year = new Date().getFullYear();
year_elm.innerHTML = year;
