/**
 * CivicLink Client Side Scripts
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Handle Admin Update Modal Population
    const updateModal = document.getElementById('updateComplaintModal');
    if (updateModal) {
        updateModal.addEventListener('show.bs.modal', function (event) {
            // Button that triggered the modal
            const button = event.relatedTarget;
            
            // Extract info from data-bs-* attributes
            const complaintId = button.getAttribute('data-bs-id');
            const currentStatus = button.getAttribute('data-bs-status');
            const currentDept = button.getAttribute('data-bs-dept');
            
            // Update the modal's content
            const modalForm = updateModal.querySelector('#updateComplaintForm');
            const modalTitle = updateModal.querySelector('.modal-title');
            const statusSelect = updateModal.querySelector('#modalStatusSelect');
            const deptSelect = updateModal.querySelector('#modalDeptSelect');
            const resolutionSection = updateModal.querySelector('#modalResolutionSection');
            
            // Set dynamic Action URL on form
            modalForm.action = `/admin/update-complaint/${complaintId}`;
            modalTitle.textContent = `Update Complaint #${complaintId}`;
            
            // Set dropdown values
            if (statusSelect) statusSelect.value = currentStatus || 'Pending';
            if (deptSelect) deptSelect.value = currentDept || 'Sanitation Department';
            
            // Show/hide resolution image section based on status
            toggleResolutionUpload(statusSelect.value, resolutionSection);
            
            // Re-bind change event on status select inside modal
            statusSelect.addEventListener('change', function () {
                toggleResolutionUpload(this.value, resolutionSection);
            });
        });
    }

    // Helper to toggle resolution image field
    function toggleResolutionUpload(status, container) {
        if (container) {
            if (status === 'Resolved') {
                container.classList.remove('d-none');
                container.querySelector('input').setAttribute('required', 'required');
            } else {
                container.classList.add('d-none');
                container.querySelector('input').removeAttribute('required');
            }
        }
    }

    // 2. Validate client-side image uploads size and extension
    const uploadInputs = document.querySelectorAll('input[type="file"]');
    uploadInputs.forEach(input => {
        input.addEventListener('change', function () {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const fileSizeMB = file.size / (1024 * 1024);
                const allowedExtensions = ['png', 'jpg', 'jpeg', 'gif', 'webp'];
                const fileExt = file.name.split('.').pop().toLowerCase();
                
                if (fileSizeMB > 10) {
                    alert('Maximum file size allowed is 10MB. Please upload a smaller image.');
                    this.value = '';
                    return;
                }
                
                if (!allowedExtensions.includes(fileExt)) {
                    alert('Invalid file format. Please upload PNG, JPG, JPEG, GIF, or WEBP.');
                    this.value = '';
                    return;
                }
            }
        });
    });

    // 3. Automatically fade out alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});
