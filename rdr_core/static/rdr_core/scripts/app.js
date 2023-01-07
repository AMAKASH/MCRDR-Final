// dataset page

let index = -1;
let runcaseObject = [];
let rows = document.getElementsByClassName("table-row");
let current_rule = -1;
let default_cornerstone_row = document
  .getElementById("addRule_corner_case")
  .cloneNode(true);

for (let row of rows) {
  addListeners(row);
}

function addListeners(item) {
  item.addEventListener("dblclick", () => {
    index = parseInt(item.cells[0].innerHTML);
    let add_rule_cur_case = document.getElementById("addRule_cur_case");
    for (let j = 1; j < add_rule_cur_case.cells.length - 1; j++) {
      add_rule_cur_case.cells[j].innerHTML = item.cells[j].innerHTML;
    }
    if (add_rule_cur_case.cells.length != item.cells.length + 1) {
      add_rule_cur_case.cells[add_rule_cur_case.cells.length - 1].innerHTML =
        item.cells[item.cells.length - 3].innerHTML;
    }
    //console.log(index);
    $("#ModalCenter").modal("show");
  });
}
let closes = document.getElementsByClassName("close");

for (let close of closes) {
  close.addEventListener("click", () => {
    resetCornerStone();
    $("#ModalCenter").modal("hide");
  });
}

function runCaseAction() {
  resetColor_Match();
  if (runcaseObject.length == 0) {
    resetCornerStone();
    const xhr = new XMLHttpRequest();
    xhr.open("GET", `/case/evaluate?index=${index}`);
    xhr.send();
    xhr.responseType = "json";
    xhr.onload = () => {
      if (xhr.readyState == 4 && xhr.status == 200) {
        const data = xhr.response;
        console.log(data);
        if (!data.eval) {
          let elm = document.getElementById("msg-area");
          elm.innerHTML = data.msg;
          elm.style.color = "#800000";
        } else {
          runcaseObject = data.eval_data;
          showCornerStoneCase();
        }
      } else {
        console.log(`Error: ${xhr.status}`);
      }
    };
  } else {
    showCornerStoneCase();
  }
}

function showCornerStoneCase() {
  let cornercase_row = document.getElementById("addRule_corner_case");
  let add_rule_cur_case = document.getElementById("addRule_cur_case");

  let current_cornerstone = runcaseObject.shift();

  if (current_cornerstone.rule_no == current_rule) {
    return;
  }
  for (let i = 0; i < current_cornerstone.cornerstone.length; i++) {
    cornercase_row.cells[i + 1].innerHTML = current_cornerstone.cornerstone[i];
  }
  cornercase_row.cells[cornercase_row.cells.length - 1].innerHTML =
    current_cornerstone.conclusion;
  add_rule_cur_case.cells[cornercase_row.cells.length - 1].innerHTML =
    current_cornerstone.conclusion;

  current_rule = current_cornerstone.rule_no;

  for (let i = 0; i < cornercase_row.cells.length; i++) {
    if (
      cornercase_row.cells[i].innerHTML.trim() ==
      add_rule_cur_case.cells[i].innerHTML.trim()
    ) {
      cornercase_row.cells[i].style.backgroundColor = "#A3EBB1";
      add_rule_cur_case.cells[i].style.backgroundColor = "#A3EBB1";
    }
  }

  let final_conclusion = document.getElementById("final-conclusion-msg");
  final_conclusion.innerHTML = final_conclusion.innerHTML.concat(
    `&lt;${current_cornerstone.conclusion}&gt; `
  );
}

async function addRuleAction() {
  let input_payload = {};
  const form = document.getElementById("add-rule-form");
  const inputs = form.getElementsByClassName("form-control");
  for (let input of inputs) {
    input_payload[input.name] = input.value;
  }

  if (input_payload["conclusion"] == "") {
    let elm = document.getElementById("msg-area");
    elm.innerHTML = "Conclusion cannot be empty";
    elm.style.color = "#800000";
  } else {
    let elm = document.getElementById("msg-area");
    elm.innerHTML = "";
  }

  input_payload["case"] = index;
  input_payload["parent"] = current_rule;

  const response = await fetch("/rules/add", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input_payload),
  });

  const data = await response.json();
  console.log(data);
  let data2 = "";
  if (data.error) {
    runcaseObject = [data.eval_data];
    resetColor_Match();
    showCornerStoneCase();
    Swal.fire({
      title: "Cornerstone Case Triggered!!!",
      text: data.msg,
      icon: "info",
      showCancelButton: true,
      showDenyButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      denyButtonColor: "#29AB87",
      confirmButtonText: "Update Conclusion",
      denyButtonText: "Add as New Rule",
    }).then(async (result) => {
      if (result.isConfirmed) {
        const response2 = await fetch("/rules/update_conclusion", {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            update_rule_no: data.eval_data.rule_no,
            new_conclusion: input_payload["conclusion"],
          }),
        });
        data2 = await response2.json();
        if (!data2.error) {
          Swal.fire("Done!", data2.msg, "success");
          resetCornerStone();
          $("#ModalCenter").modal("hide");
        }
      } else if (result.isDenied) {
        input_payload["parent"] = -2;
        const response2 = await fetch("/rules/add", {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(input_payload),
        });
        data2 = await response2.json();
        if (!data2.error) {
          Swal.fire("Done!", data2.msg, "success");
          resetCornerStone();
          $("#ModalCenter").modal("hide");
        }
      }
    });
  } else {
    Swal.fire("Rule Added", data.msg, "success");
    resetCornerStone();
    $("#ModalCenter").modal("hide");
  }
}

function resetCornerStone() {
  runcaseObject = [];
  let temp = document.getElementById("addRule_corner_case");
  let final_conclusion = document.getElementById("final-conclusion-msg");
  let elm = document.getElementById("msg-area");
  const form = document.getElementById("add-rule-form");
  const inputs = form.getElementsByClassName("form-control");

  temp.innerHTML = default_cornerstone_row.innerHTML;
  current_rule = -1;
  elm.innerHTML = "";
  final_conclusion.innerHTML = "";
  for (let input of inputs) {
    input.value = "";
  }
  resetColor_Match();
}

function resetColor_Match() {
  let add_rule_cur_case = document.getElementById("addRule_cur_case");
  let cornercase_row = document.getElementById("addRule_corner_case");
  for (let i = 0; i < add_rule_cur_case.cells.length; i++) {
    add_rule_cur_case.cells[i].style.backgroundColor = "";
    cornercase_row.cells[i].style.backgroundColor = "";
  }

  add_rule_cur_case.cells[cornercase_row.cells.length - 1].innerHTML =
    "&#x254D;";
}
