document.addEventListener("DOMContentLoaded", function(){
  function enableShowAll(buttonId, containerId){
    const btn = document.getElementById(buttonId);
    const grid = document.getElementById(containerId);
    if (!btn || !grid) return;
    btn.addEventListener("click", function(){
      grid.classList.add("show-all");
      btn.remove();
    });
  }
  // activează pentru categorii și (opțional) servicii populare
  enableShowAll("showAllCats", "catGrid");
  enableShowAll("showAllPopular", "popularGrid");
  enableShowAll("showAllMyServices", "myServicesGrid");
});
