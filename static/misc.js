$("#login").click(function()
{
		$('#loginform').slideToggle();
		return
		if($('#loginform').is(":hidden"))
		{
				$('#loginform').slideDown();
		}
		else
		{
				$('#loginform').slideUp();
		}
}
);

$('#loginform').slideToggle(0);
