frappe.provide("chemical");

chemical.CompanyAndItemDefaults = class StockController extends frappe.ui.form.Controller {
    async setup() {
        await this.get_maintain_as_is_new();
    }

    async get_maintain_as_is_new() {
        this.frm.maintain_as_is_new = 0;
        if (this.frm.doc.company){
            await frappe.db.get_value("Company", this.frm.doc.company, "maintain_as_is_new").then(
                (response) => {
                    var data = response['message'];
                    this.frm.maintain_as_is_new = data['maintain_as_is_new'];
                }
            )
        }
    }
}