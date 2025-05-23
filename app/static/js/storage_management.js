/**
 * Storage Management Functions
 * Provides functionality for bulk moving parts between storage locations
 */

// Add a button to the page header for bulk move operations
function addBulkMoveButton(selector) {
  const buttonHtml = `
    <a href="/atv/storage/bulk-move" class="btn btn-primary ml-2">
      <i class="fas fa-exchange-alt"></i> Bulk Move Parts
    </a>
  `;
  
  $(selector).append(buttonHtml);
}

// Initialize storage bulk move functionality
$(document).ready(function() {
  // Add bulk move button to storage list page
  if (window.location.pathname === '/atv/storage') {
    addBulkMoveButton('.page-actions');
  }
  
  // Handle bulk move form validation
  $('.bulk-move-form').on('submit', function(e) {
    const sourceId = $(this).find('[name="source_id"]').val();
    const destinationId = $(this).find('[name="destination_id"]').val();
    
    if (sourceId === destinationId) {
      e.preventDefault();
      alert('Source and destination storage cannot be the same.');
      return false;
    }
    
    return true;
  });
  
  // Update move summary when selections change
  $('.bulk-move-form select').on('change', function() {
    const form = $(this).closest('form');
    const sourceId = form.find('[name="source_id"]').val();
    const destinationId = form.find('[name="destination_id"]').val();
    
    if (sourceId && destinationId && sourceId !== destinationId) {
      const sourceOption = form.find('[name="source_id"] option:selected');
      const destinationOption = form.find('[name="destination_id"] option:selected');
      
      const sourceName = sourceOption.text().split(' (')[0];
      const destinationName = destinationOption.text().split(' (')[0];
      const partsCount = sourceOption.data('parts-count');
      
      form.find('.source-name').text(sourceName);
      form.find('.destination-name').text(destinationName);
      form.find('.parts-count').text(partsCount);
      
      form.find('.move-summary').show();
      form.find('[type="submit"]').prop('disabled', partsCount === 0);
    } else {
      form.find('.move-summary').hide();
      form.find('[type="submit"]').prop('disabled', true);
    }
  });
});
